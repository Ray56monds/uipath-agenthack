"""Tests for the Resolution Agent."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.resolution.agent import ResolutionAgent


class TestResolutionAgent:
    def test_agent_initializes(self):
        with patch("agents.resolution.agent.ChatAnthropic"):
            agent = ResolutionAgent()
            assert agent.llm is not None
            assert agent.chain is not None

    @pytest.mark.asyncio
    async def test_draft_resolution_billing(self):
        with patch("agents.resolution.agent.ChatAnthropic"):
            agent = ResolutionAgent()
            mock_result = {
                "draft_response": "Dear customer, we apologize for the billing error...",
                "internal_notes": "Refund approved per policy",
                "suggested_actions": ["issue_refund", "apply_credit"],
                "compensation_recommendation": "$50 credit",
                "requires_human_approval": True,
                "approval_reason": "Refund over $25 threshold",
                "escalate_to": ""
            }
            agent.chain = MagicMock()
            agent.chain.ainvoke = AsyncMock(return_value=mock_result)

            result = await agent.draft_resolution({
                "subject": "Overcharged $500",
                "body": "I was overcharged",
                "category": "billing",
                "urgency_score": 0.8,
                "customer_tier": "platinum"
            })
            assert result["requires_human_approval"] is True
            assert "issue_refund" in result["suggested_actions"]

    @pytest.mark.asyncio
    async def test_auto_resolve_simple_inquiry(self):
        with patch("agents.resolution.agent.ChatAnthropic"):
            agent = ResolutionAgent()
            mock_result = {
                "draft_response": "You can update your address in Settings > Profile.",
                "internal_notes": "Simple self-service inquiry",
                "suggested_actions": ["send_instructions"],
                "compensation_recommendation": "none",
                "requires_human_approval": False,
                "approval_reason": "",
                "escalate_to": ""
            }
            agent.chain = MagicMock()
            agent.chain.ainvoke = AsyncMock(return_value=mock_result)

            result = await agent.draft_resolution({
                "subject": "Update address",
                "body": "How do I update my address?",
                "category": "account",
                "urgency_score": 0.2,
                "customer_tier": "standard"
            })
            assert result["requires_human_approval"] is False

    @pytest.mark.asyncio
    async def test_legal_threat_requires_approval(self):
        with patch("agents.resolution.agent.ChatAnthropic"):
            agent = ResolutionAgent()
            mock_result = {
                "draft_response": "We take this matter seriously...",
                "internal_notes": "Legal threat detected - route to legal",
                "suggested_actions": ["route_to_legal", "escalate_manager"],
                "compensation_recommendation": "none",
                "requires_human_approval": True,
                "approval_reason": "Legal threat requires legal team review",
                "escalate_to": "legal"
            }
            agent.chain = MagicMock()
            agent.chain.ainvoke = AsyncMock(return_value=mock_result)

            result = await agent.draft_resolution({
                "subject": "Disputed charges",
                "body": "I'm contacting my lawyer",
                "category": "billing",
                "urgency_score": 0.95,
                "escalation_flags": ["legal_threat"],
                "customer_tier": "gold"
            })
            assert result["requires_human_approval"] is True
            assert "route_to_legal" in result["suggested_actions"]
