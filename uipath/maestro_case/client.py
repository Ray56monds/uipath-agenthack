"""
UiPath Maestro Case API Client.

Connects our Python agents to UiPath Automation Cloud
to create/update cases, transition stages, and manage Action Center tasks.
"""

import httpx
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

UIPATH_TENANT_URL = os.getenv("UIPATH_TENANT_URL", "")
UIPATH_CLIENT_ID = os.getenv("UIPATH_CLIENT_ID", "")
UIPATH_CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET", "")


class UiPathClient:
    """Client for UiPath Orchestrator and Maestro Case APIs."""

    def __init__(self):
        self.base_url = UIPATH_TENANT_URL
        self.token = None

    async def authenticate(self):
        """Get OAuth2 token from UiPath Identity Server."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://cloud.uipath.com/identity_/connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": UIPATH_CLIENT_ID,
                    "client_secret": UIPATH_CLIENT_SECRET,
                    "scope": "OR.Cases OR.Tasks OR.Execution",
                },
            )
            resp.raise_for_status()
            self.token = resp.json()["access_token"]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def create_case(self, case_data: dict) -> dict:
        """Create a new case in Maestro."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/maestro_/api/v1/cases",
                headers=self._headers(),
                json={
                    "definitionId": case_data.get("definition_id"),
                    "title": case_data.get("subject", "New Escalation"),
                    "priority": case_data.get("priority", "medium"),
                    "fields": {
                        "customer_id": case_data.get("customer_id"),
                        "customer_tier": case_data.get("customer_tier", "standard"),
                        "ticket_id": case_data.get("ticket_id"),
                        "source": case_data.get("source"),
                        "subject": case_data.get("subject"),
                        "body": case_data.get("body"),
                    },
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def update_case_fields(self, case_id: str, fields: dict) -> dict:
        """Update case fields (e.g., after triage or enrichment)."""
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.base_url}/maestro_/api/v1/cases/{case_id}",
                headers=self._headers(),
                json={"fields": fields},
            )
            resp.raise_for_status()
            return resp.json()

    async def transition_stage(self, case_id: str, target_stage: str) -> dict:
        """Move case to the next stage."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/maestro_/api/v1/cases/{case_id}/transition",
                headers=self._headers(),
                json={"targetStage": target_stage},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_action(self, case_id: str, action_data: dict) -> dict:
        """Create a human task in Action Center."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/maestro_/api/v1/cases/{case_id}/actions",
                headers=self._headers(),
                json={
                    "title": action_data.get("title"),
                    "type": action_data.get("type", "approval"),
                    "assignee": action_data.get("assignee"),
                    "data": action_data.get("data", {}),
                    "actions": action_data.get("actions", ["approve", "reject"]),
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_case(self, case_id: str) -> dict:
        """Get case details."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/maestro_/api/v1/cases/{case_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def add_audit_entry(self, case_id: str, actor: str, actor_type: str, action: str, details: dict = None) -> dict:
        """Add an entry to the case audit trail."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/maestro_/api/v1/cases/{case_id}/comments",
                headers=self._headers(),
                json={
                    "text": f"[{actor_type.upper()}] {actor}: {action}",
                    "metadata": details or {},
                },
            )
            resp.raise_for_status()
            return resp.json()


async def run_full_pipeline(ticket: dict):
    """
    End-to-end pipeline: Intake → Triage → Enrich → Resolve → Satisfaction.
    This is what UiPath API Workflows call.
    """
    from agents.triage.agent import triage_ticket
    from agents.context.agent import ContextAgent
    from agents.resolution.agent import ResolutionAgent
    from agents.satisfaction.agent import SatisfactionAgent

    client = UiPathClient()
    await client.authenticate()

    # 1. Create case
    case = await client.create_case(ticket)
    case_id = case["id"]

    # 2. Triage
    triage_result = triage_ticket(ticket)
    await client.update_case_fields(case_id, triage_result)
    await client.transition_stage(case_id, "Enrichment")

    # 3. Enrich
    context_agent = ContextAgent()
    context_brief = await context_agent.enrich_case(ticket["customer_id"], ticket)
    await client.update_case_fields(case_id, {"context_brief": context_brief})
    await client.transition_stage(case_id, "Resolution")

    # 4. Resolve
    resolution_agent = ResolutionAgent()
    case_data = {**ticket, **triage_result, "context_brief": context_brief}
    resolution = await resolution_agent.draft_resolution(case_data)
    await client.update_case_fields(case_id, resolution)

    # 5. Human approval if needed
    if resolution.get("requires_human_approval"):
        await client.create_action(case_id, {
            "title": f"Approve resolution for {ticket['subject']}",
            "type": "approval",
            "assignee": triage_result.get("recommended_team", "support"),
            "data": resolution,
            "actions": ["approve", "reject", "modify_and_approve"],
        })
    else:
        await client.transition_stage(case_id, "Satisfaction")

        # 6. Satisfaction check
        sat_agent = SatisfactionAgent()
        sat_result = await sat_agent.analyze_satisfaction({"case": case_data, "resolution": resolution})
        await client.update_case_fields(case_id, sat_result)

        if sat_result.get("action") == "close_case":
            await client.transition_stage(case_id, "Closed")

    return {"case_id": case_id, "status": "processed"}
