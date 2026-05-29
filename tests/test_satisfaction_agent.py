"""Tests for the Satisfaction Agent."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.satisfaction.agent import SatisfactionAgent


class TestSatisfactionAgent:
    def test_agent_initializes(self):
        with patch("agents.satisfaction.agent.ChatAnthropic"):
            agent = SatisfactionAgent()
            assert agent.llm is not None

    @pytest.mark.asyncio
    async def test_positive_feedback(self):
        with patch("agents.satisfaction.agent.ChatAnthropic"):
            agent = SatisfactionAgent()
            agent.satisfaction_chain = MagicMock()
            agent.satisfaction_chain.ainvoke = AsyncMock(return_value={
                "satisfaction_score": 0.9,
                "sentiment": "positive",
                "follow_up_required": False,
                "follow_up_timing": "1_week",
                "key_factors": ["fast_resolution"]
            })
            agent.churn_chain = MagicMock()
            agent.churn_chain.ainvoke = AsyncMock(return_value={
                "churn_probability": 0.05,
                "risk_factors": [],
                "retention_actions": [],
                "trigger_outreach": False,
                "action": "close_case"
            })

            result = await agent.analyze_satisfaction({
                "case": {"case_id": "CASE-001", "customer_tier": "standard"},
                "resolution": {"draft_response": "Issue resolved quickly!"}
            })
            assert result["satisfaction_score"] > 0.8
            assert result["churn_probability"] < 0.2
            assert result["action"] == "close_case"

    @pytest.mark.asyncio
    async def test_negative_feedback_triggers_reescalation(self):
        with patch("agents.satisfaction.agent.ChatAnthropic"):
            agent = SatisfactionAgent()
            agent.satisfaction_chain = MagicMock()
            agent.satisfaction_chain.ainvoke = AsyncMock(return_value={
                "satisfaction_score": 0.1,
                "sentiment": "negative",
                "follow_up_required": True,
                "follow_up_timing": "immediate",
                "key_factors": ["slow_resolution", "unresolved_issue"]
            })
            agent.churn_chain = MagicMock()
            agent.churn_chain.ainvoke = AsyncMock(return_value={
                "churn_probability": 0.85,
                "risk_factors": ["unresolved", "long_wait", "negative_sentiment"],
                "retention_actions": ["manager_call", "compensation"],
                "trigger_outreach": True,
                "action": "re_escalate"
            })

            result = await agent.analyze_satisfaction({
                "case": {"case_id": "CASE-003", "customer_tier": "vip"},
                "resolution": {"draft_response": "We're still working on it..."}
            })
            assert result["satisfaction_score"] < 0.3
            assert result["churn_probability"] > 0.7
            assert result["action"] == "re_escalate"
            assert result["follow_up_required"] is True

    @pytest.mark.asyncio
    async def test_neutral_feedback(self):
        with patch("agents.satisfaction.agent.ChatAnthropic"):
            agent = SatisfactionAgent()
            agent.satisfaction_chain = MagicMock()
            agent.satisfaction_chain.ainvoke = AsyncMock(return_value={
                "satisfaction_score": 0.5,
                "sentiment": "neutral",
                "follow_up_required": True,
                "follow_up_timing": "48h",
                "key_factors": ["adequate_resolution"]
            })
            agent.churn_chain = MagicMock()
            agent.churn_chain.ainvoke = AsyncMock(return_value={
                "churn_probability": 0.4,
                "risk_factors": ["slow_response"],
                "retention_actions": ["follow_up_survey"],
                "trigger_outreach": False,
                "action": "follow_up"
            })

            result = await agent.analyze_satisfaction({
                "case": {"case_id": "CASE-007", "customer_tier": "standard"},
                "resolution": {"draft_response": "Your issue has been addressed."}
            })
            assert 0.3 < result["satisfaction_score"] < 0.7
            assert result["action"] == "follow_up"
