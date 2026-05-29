"""Tests for mock FastAPI services."""
import pytest
from httpx import AsyncClient, ASGITransport
from services.mock_crm.main import app as crm_app
from services.mock_tickets.main import app as tickets_app


class TestMockCRM:
    @pytest.mark.asyncio
    async def test_get_existing_customer(self):
        transport = ASGITransport(app=crm_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/customers/CUST-001")
            assert response.status_code == 200
            data = response.json()
            assert data["customer_id"] == "CUST-001"
            assert data["tier"] == "vip"
            assert data["lifetime_value"] == 125000

    @pytest.mark.asyncio
    async def test_get_nonexistent_customer(self):
        transport = ASGITransport(app=crm_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/customers/CUST-999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_customer_history(self):
        transport = ASGITransport(app=crm_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/customers/CUST-001/history")
            assert response.status_code == 200
            data = response.json()
            assert "interactions" in data

    @pytest.mark.asyncio
    async def test_health_check_crm(self):
        transport = ASGITransport(app=crm_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


class TestMockTickets:
    @pytest.mark.asyncio
    async def test_get_pending_tickets(self):
        transport = ASGITransport(app=tickets_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/tickets/pending")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    @pytest.mark.asyncio
    async def test_create_ticket(self):
        transport = ASGITransport(app=tickets_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ticket = {
                "subject": "Test ticket",
                "body": "This is a test",
                "source": "email",
                "customer_id": "CUST-001"
            }
            response = await client.post("/tickets", json=ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["customer_id"] == "CUST-001"
            assert data["status"] == "new"

    @pytest.mark.asyncio
    async def test_health_check_tickets(self):
        transport = ASGITransport(app=tickets_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self):
        transport = ASGITransport(app=tickets_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/tickets/TKT-1001")
            assert response.status_code == 200
            assert response.json()["customer_id"] == "CUST-001"
