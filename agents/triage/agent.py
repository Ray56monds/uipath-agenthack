"""
Triage Agent - Classifies urgency, detects intent & sentiment.

In production, this runs as a UiPath Agent Builder agent.
This file serves as the logic reference and local testing harness.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../../config/.env"))

TRIAGE_SYSTEM_PROMPT = """You are a customer escalation triage agent. Analyze the incoming ticket and produce a structured triage assessment.

You must determine:
1. **urgency_score** (0.0 to 1.0): How urgent is this?
2. **sentiment_score** (-1.0 to 1.0): Customer sentiment from very negative (-1) to very positive (1).
3. **intent**: What does the customer want? (e.g., "refund", "technical_fix", "information", "escalation", "cancellation")
4. **category**: One of: billing, technical, account, complaint, legal, general
5. **recommended_team**: Which team should handle this?
6. **flags**: Array of special flags (e.g., "legal_threat", "vip_customer", "social_media_public", "churn_risk")
7. **summary**: One-sentence summary of the issue.

Rules:
- If customer mentions lawyer, legal action, or lawsuit → flag "legal_threat", urgency >= 0.9
- If source is social_media → flag "social_media_public", urgency += 0.2
- If sentiment < -0.5 and customer has high lifetime value → flag "churn_risk"
"""


class TriageResult(BaseModel):
    urgency_score: float = Field(description="Urgency from 0.0 to 1.0")
    sentiment_score: float = Field(description="Sentiment from -1.0 to 1.0")
    intent: str = Field(description="Customer intent")
    category: str = Field(description="Issue category")
    recommended_team: str = Field(description="Team to handle this")
    flags: list[str] = Field(description="Special flags detected")
    summary: str = Field(description="One-sentence summary")


class TriageAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.parser = JsonOutputParser(pydantic_object=TriageResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", TRIAGE_SYSTEM_PROMPT + "\n\n{format_instructions}"),
            ("human", "Ticket Source: {source}\nSubject: {subject}\nBody: {body}\nCustomer Tier: {customer_tier}"),
        ])
        self.chain = self.prompt | self.llm | self.parser

    def run(self, ticket: dict) -> dict:
        """Triage a ticket and return structured assessment."""
        return self.chain.invoke({
            "source": ticket.get("source", ticket.get("channel", "unknown")),
            "subject": ticket.get("subject", ""),
            "body": ticket.get("body", ""),
            "customer_tier": ticket.get("customer_tier", "standard"),
            "format_instructions": self.parser.get_format_instructions(),
        })


def triage_ticket(ticket: dict, customer_tier: str = "standard") -> dict:
    """Convenience function for triaging a ticket."""
    agent = TriageAgent()
    ticket["customer_tier"] = customer_tier
    return agent.run(ticket)


if __name__ == "__main__":
    test_ticket = {
        "source": "chat",
        "subject": "Billing charge I never authorized",
        "body": "I was charged $499 for a service I never signed up for. I want an immediate refund or I will be contacting my lawyer.",
    }
    result = triage_ticket(test_ticket, customer_tier="standard")
    print("Triage Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
