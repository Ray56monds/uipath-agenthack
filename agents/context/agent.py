"""
Context Agent - Enriches escalation cases with customer history from CRM.

Framework: LangChain
LLM: Claude 3.5 Sonnet (Anthropic)
Role: Pulls customer data, interaction history, and generates a context brief.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import httpx
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../../config/.env"))

CRM_SERVICE_URL = os.getenv("CRM_SERVICE_URL", "http://localhost:8001")

CONTEXT_PROMPT = """You are a context enrichment agent for customer escalation cases.

Given the customer data and interaction history below, produce a context brief that helps the resolution team understand:
- Who this customer is and their value to the business
- Recent interaction patterns and sentiment trends
- Any relevant history that explains the current escalation
- Risk factors (churn risk, legal history, social media activity)
- Recommended approach for handling this customer

Customer Data:
{customer_data}

Interaction History:
{interaction_history}

Current Ticket:
Subject: {subject}
Body: {body}
Category: {category}
Urgency: {urgency_score}

Produce a concise context brief."""


class ContextAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.chain = (
            ChatPromptTemplate.from_template(CONTEXT_PROMPT)
            | self.llm
            | StrOutputParser()
        )

    def _fetch_customer(self, customer_id: str) -> dict:
        try:
            resp = httpx.get(f"{CRM_SERVICE_URL}/customers/{customer_id}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return {"error": "Customer not found"}

    def _fetch_history(self, customer_id: str) -> list:
        try:
            resp = httpx.get(f"{CRM_SERVICE_URL}/customers/{customer_id}/history", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return []

    async def enrich_case(self, customer_id: str, case: dict = None) -> str:
        """Enrich a case with customer context."""
        if case is None:
            case = {}
        customer_data = self._fetch_customer(customer_id)
        history = self._fetch_history(customer_id)
        result = await self.chain.ainvoke({
            "customer_data": str(customer_data),
            "interaction_history": str(history),
            "subject": case.get("subject", ""),
            "body": case.get("body", ""),
            "category": case.get("category", "general"),
            "urgency_score": case.get("urgency_score", 0.5),
        })
        return result


def enrich_case(case: dict) -> str:
    """Synchronous convenience function for enriching a case."""
    agent = ContextAgent()
    customer_data = agent._fetch_customer(case.get("customer_id", "unknown"))
    history = agent._fetch_history(case.get("customer_id", "unknown"))
    chain = (
        ChatPromptTemplate.from_template(CONTEXT_PROMPT)
        | agent.llm
        | StrOutputParser()
    )
    return chain.invoke({
        "customer_data": str(customer_data),
        "interaction_history": str(history),
        "subject": case.get("subject", ""),
        "body": case.get("body", ""),
        "category": case.get("category", "general"),
        "urgency_score": case.get("urgency_score", 0.5),
    })


if __name__ == "__main__":
    test_case = {
        "customer_id": "CUST-001",
        "subject": "API response times unacceptable",
        "body": "Our integration has been experiencing 5-10 second response times since last Tuesday.",
        "category": "technical",
        "urgency_score": 0.8,
    }
    brief = enrich_case(test_case)
    print("Context Brief:")
    print(brief)
