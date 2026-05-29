"""
Resolution Agent - Drafts customer responses and suggests resolution actions.

Framework: LangChain
LLM: Claude 3.5 Sonnet (Anthropic)
Role: Takes triage data + context brief and produces a draft response,
      suggested actions, and compensation recommendations for human approval.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../../config/.env"))

RESOLUTION_SYSTEM_PROMPT = """You are a customer resolution agent. Draft a professional response and recommend actions.

Guidelines:
- Match tone to severity: empathetic for frustrated customers, professional for business inquiries
- For VIP/Enterprise customers: prioritize retention, offer proactive solutions
- For legal threats: acknowledge concern, do NOT admit fault, recommend legal team review
- For billing disputes: offer clear next steps, mention refund process if applicable
- Always include a clear next step for the customer

Produce JSON with:
- draft_response: The message to send to the customer
- internal_notes: Notes for the support team
- suggested_actions: Array of concrete actions
- compensation_recommendation: What to offer (credit, refund, extension, or "none")
- requires_human_approval: Boolean - does this need human sign-off?
- approval_reason: If human approval needed, why?
- escalate_to: If further escalation needed, which team?
"""


class ResolutionOutput(BaseModel):
    draft_response: str = Field(description="Customer-facing response draft")
    internal_notes: str = Field(description="Internal notes for support team")
    suggested_actions: list[str] = Field(description="Concrete actions to take")
    compensation_recommendation: str = Field(description="Compensation to offer")
    requires_human_approval: bool = Field(description="Whether human must approve")
    approval_reason: str = Field(description="Why human approval is needed")
    escalate_to: str = Field(description="Further escalation target")


class ResolutionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.parser = JsonOutputParser(pydantic_object=ResolutionOutput)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", RESOLUTION_SYSTEM_PROMPT + "\n\n{format_instructions}"),
            ("human", """Case Details:
- Subject: {subject}
- Category: {category}
- Urgency: {urgency_score}
- Sentiment: {sentiment_score}
- Intent: {intent}
- Flags: {flags}
- Customer Tier: {customer_tier}

Context Brief:
{context_brief}

Original Message:
{body}"""),
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def draft_resolution(self, case: dict) -> dict:
        """Generate resolution recommendation for a case."""
        return await self.chain.ainvoke({
            "subject": case.get("subject", case.get("summary", "")),
            "body": case.get("body", ""),
            "category": case.get("category", "general"),
            "urgency_score": case.get("urgency_score", case.get("urgency", 0.5)),
            "sentiment_score": case.get("sentiment_score", case.get("sentiment", 0.0)),
            "intent": case.get("intent", "unknown"),
            "flags": ", ".join(case.get("flags", case.get("escalation_flags", []))),
            "customer_tier": case.get("customer_tier", "standard"),
            "context_brief": case.get("context_brief", "No context available"),
            "format_instructions": self.parser.get_format_instructions(),
        })


def resolve_case(case: dict, context_brief: str) -> dict:
    """Synchronous convenience function for resolving a case."""
    agent = ResolutionAgent()
    case["context_brief"] = context_brief
    import asyncio
    return asyncio.run(agent.draft_resolution(case))


if __name__ == "__main__":
    test_case = {
        "subject": "Billing charge I never authorized",
        "body": "I was charged $499 for a service I never signed up for. I want an immediate refund or I will be contacting my lawyer.",
        "category": "billing",
        "urgency_score": 0.9,
        "sentiment_score": -0.8,
        "intent": "refund",
        "flags": ["legal_threat", "churn_risk"],
        "customer_tier": "standard",
    }
    test_context = "Customer has been with us 6 months. LTV $5,200. Sentiment trending negative."
    result = resolve_case(test_case, test_context)
    print("Resolution Output:")
    for k, v in result.items():
        print(f"  {k}: {v}")
