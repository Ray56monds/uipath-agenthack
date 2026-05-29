"""
Satisfaction Agent - Post-resolution analysis and churn prediction.

Framework: LangChain (multi-step chain)
LLM: Claude 3.5 Sonnet (Anthropic)
Role: After a case is resolved, this agent analyzes the outcome,
      predicts churn risk, and recommends follow-up actions.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import os
import json

load_dotenv(os.path.join(os.path.dirname(__file__), "../../config/.env"))

SATISFACTION_PROMPT = """You are a Customer Satisfaction Analyst. Analyze the resolved case and predict satisfaction.

Case Subject: {subject}
Customer Tier: {customer_tier}
Urgency Score: {urgency_score}
Sentiment at Intake: {sentiment_score}
Resolution: {draft_response}
Actions Taken: {suggested_actions}
Compensation: {compensation}

Return JSON with:
- satisfaction_score: float 0.0-1.0
- sentiment: "positive", "neutral", or "negative"
- follow_up_required: boolean
- follow_up_timing: "immediate", "24h", "48h", or "1_week"
- key_factors: list of strings"""

CHURN_PROMPT = """You are a Churn Risk Analyst. Based on the satisfaction analysis and case details, assess churn risk.

Customer Tier: {customer_tier}
Lifetime Value: {lifetime_value}
Satisfaction Score: {satisfaction_score}
Sentiment: {sentiment}
Flags: {flags}
Resolution Required Human Approval: {requires_human_approval}

Return JSON with:
- churn_probability: float 0.0-1.0
- risk_factors: list of top 3 strings
- retention_actions: list of recommended actions
- trigger_outreach: boolean
- action: "close_case", "follow_up", or "re_escalate" """


class SatisfactionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        self.satisfaction_chain = (
            ChatPromptTemplate.from_template(SATISFACTION_PROMPT)
            | self.llm
            | JsonOutputParser()
        )
        self.churn_chain = (
            ChatPromptTemplate.from_template(CHURN_PROMPT)
            | self.llm
            | JsonOutputParser()
        )

    async def analyze_satisfaction(self, feedback: dict) -> dict:
        """Run satisfaction + churn analysis pipeline."""
        case = feedback.get("case", feedback)
        resolution = feedback.get("resolution", {})

        # Step 1: Satisfaction analysis
        sat_result = await self.satisfaction_chain.ainvoke({
            "subject": case.get("subject", case.get("case_id", "")),
            "customer_tier": case.get("customer_tier", "standard"),
            "urgency_score": case.get("urgency_score", 0.5),
            "sentiment_score": case.get("sentiment_score", 0.0),
            "draft_response": resolution.get("draft_response", case.get("comment", "")),
            "suggested_actions": json.dumps(resolution.get("suggested_actions", [])),
            "compensation": resolution.get("compensation", "none"),
        })

        # Step 2: Churn prediction
        churn_result = await self.churn_chain.ainvoke({
            "customer_tier": case.get("customer_tier", "standard"),
            "lifetime_value": case.get("lifetime_value", "unknown"),
            "satisfaction_score": sat_result.get("satisfaction_score", 0.5),
            "sentiment": sat_result.get("sentiment", "neutral"),
            "flags": json.dumps(case.get("flags", [])),
            "requires_human_approval": resolution.get("requires_human_approval", False),
        })

        return {
            "satisfaction_score": sat_result.get("satisfaction_score", 0.5),
            "sentiment": sat_result.get("sentiment", "neutral"),
            "churn_probability": churn_result.get("churn_probability", 0.5),
            "action": churn_result.get("action", "follow_up"),
            "follow_up_required": sat_result.get("follow_up_required", True),
            "risk_factors": churn_result.get("risk_factors", []),
            "retention_actions": churn_result.get("retention_actions", []),
        }


if __name__ == "__main__":
    import asyncio

    test_case = {
        "subject": "API response times unacceptable",
        "customer_tier": "vip",
        "urgency_score": 0.8,
        "sentiment_score": -0.4,
        "lifetime_value": 125000,
        "flags": ["churn_risk"],
    }
    test_resolution = {
        "draft_response": "We've deployed a fix. Response times should normalize within the hour.",
        "suggested_actions": ["Deploy hotfix", "Monitor 24h", "Schedule follow-up call"],
        "compensation": "1 month service credit",
        "requires_human_approval": True,
    }

    result = asyncio.run(SatisfactionAgent().analyze_satisfaction({"case": test_case, "resolution": test_resolution}))
    print("Satisfaction Analysis:")
    print(json.dumps(result, indent=2))
