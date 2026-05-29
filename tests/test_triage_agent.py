"""Tests for the Triage Agent."""
import pytest
from unittest.mock import patch, MagicMock
from agents.triage.agent import TriageAgent


class TestTriageAgent:
    def test_agent_initializes(self):
        with patch("agents.triage.agent.ChatAnthropic"):
            agent = TriageAgent()
            assert agent.llm is not None
            assert agent.chain is not None

    def test_classify_urgent_billing(self):
        with patch("agents.triage.agent.ChatAnthropic"):
            agent = TriageAgent()
            mock_result = {
                "urgency_score": 0.95,
                "sentiment_score": -0.8,
                "intent": "refund",
                "category": "billing",
                "recommended_team": "billing_support",
                "flags": ["legal_threat", "churn_risk"],
                "summary": "Customer demanding refund, threatening legal action"
            }
            with patch.object(agent, "chain") as mock_chain:
                mock_chain.invoke.return_value = mock_result
                result = agent.run({
                    "subject": "URGENT: Overcharged $5000",
                    "body": "I'm contacting my lawyer if this isn't fixed.",
                    "channel": "email",
                    "customer_id": "CUST-001"
                })
                assert result["urgency_score"] >= 0.9
                assert result["category"] == "billing"
                assert "legal_threat" in result["flags"]

    def test_classify_low_priority(self):
        with patch("agents.triage.agent.ChatAnthropic"):
            agent = TriageAgent()
            mock_result = {
                "urgency_score": 0.2,
                "sentiment_score": 0.5,
                "intent": "information_request",
                "category": "account",
                "recommended_team": "account_management",
                "flags": [],
                "summary": "Customer asking about address update"
            }
            with patch.object(agent, "chain") as mock_chain:
                mock_chain.invoke.return_value = mock_result
                result = agent.run({
                    "subject": "How do I update my address?",
                    "body": "I recently moved and need to update my billing address.",
                    "channel": "chat",
                    "customer_id": "CUST-003"
                })
                assert result["urgency_score"] < 0.5
                assert result["flags"] == []

    def test_social_media_detection(self):
        with patch("agents.triage.agent.ChatAnthropic"):
            agent = TriageAgent()
            mock_result = {
                "urgency_score": 0.9,
                "sentiment_score": -0.7,
                "intent": "complaint",
                "category": "complaint",
                "recommended_team": "social_media_team",
                "flags": ["social_media_public", "churn_risk"],
                "summary": "Public complaint on social media going viral"
            }
            with patch.object(agent, "chain") as mock_chain:
                mock_chain.invoke.return_value = mock_result
                result = agent.run({
                    "subject": "@company your product broke my workflow",
                    "body": "Posted publicly with 500 retweets.",
                    "source": "social_media",
                    "customer_id": "CUST-005"
                })
                assert result["urgency_score"] >= 0.8
                assert "social_media_public" in result["flags"]
