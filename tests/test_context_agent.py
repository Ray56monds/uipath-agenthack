"""Tests for the Context Agent."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.context.agent import ContextAgent


class TestContextAgent:
    def test_agent_initializes(self):
        with patch("agents.context.agent.ChatAnthropic"):
            agent = ContextAgent()
            assert agent.llm is not None

    @pytest.mark.asyncio
    async def test_enrich_case_calls_crm(self):
        with patch("agents.context.agent.ChatAnthropic"):
            agent = ContextAgent()
            agent._fetch_customer = MagicMock(return_value={
                "customer_id": "CUST-001",
                "name": "Alice Johnson",
                "tier": "vip",
                "lifetime_value": 125000,
            })
            agent._fetch_history = MagicMock(return_value=[
                {"date": "2025-05-15", "type": "support_call", "sentiment": 0.6}
            ])
            agent.chain = MagicMock()
            agent.chain.ainvoke = AsyncMock(return_value="VIP customer with high LTV. Handle with priority.")

            result = await agent.enrich_case("CUST-001", {"subject": "Test", "body": "Test body"})
            assert "VIP" in result
            agent._fetch_customer.assert_called_once_with("CUST-001")
            agent._fetch_history.assert_called_once_with("CUST-001")

    @pytest.mark.asyncio
    async def test_enrich_handles_unknown_customer(self):
        with patch("agents.context.agent.ChatAnthropic"):
            agent = ContextAgent()
            agent._fetch_customer = MagicMock(return_value={"error": "Customer not found"})
            agent._fetch_history = MagicMock(return_value=[])
            agent.chain = MagicMock()
            agent.chain.ainvoke = AsyncMock(return_value="Unknown customer. Standard handling.")

            result = await agent.enrich_case("CUST-999")
            assert "Unknown" in result or "Standard" in result
