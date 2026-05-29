"""Tests for the main orchestrator API."""
import pytest
from httpx import AsyncClient, ASGITransport
from orchestrator import app


class TestOrchestratorAPI:
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_intake_creates_case(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ticket = {
                "ticket_id": "TKT-TEST-001",
                "customer_id": "CUST-001",
                "source": "email",
                "subject": "Test issue",
                "body": "This is a test ticket",
                "customer_tier": "standard"
            }
            response = await client.post("/cases/intake", json=ticket)
            assert response.status_code == 200
            data = response.json()
            assert "case_id" in data
            assert data["stage"] == "intake"

    @pytest.mark.asyncio
    async def test_get_nonexistent_case(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/cases/CASE-NONEXISTENT")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_cases(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/cases")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
