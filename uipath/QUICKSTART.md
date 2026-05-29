# UiPath Quick Start for First-Time Users

## What You Need

1. **UiPath Labs Access** — Request at https://www.uipath.com/developers/labs
2. **UiPath Studio** (optional for local dev) — Download from https://www.uipath.com/studio
3. **UiPath Automation Cloud** — Your Labs access gives you a tenant

---

## How This Project Maps to UiPath

| Our Code | UiPath Component | What It Does |
|----------|-----------------|--------------|
| `orchestrator.py` | API Workflows | REST API that agents call |
| `agents/triage/` | Agent Builder | Native UiPath agent for classification |
| `agents/context/` | API Workflow trigger | Called by Maestro when case hits Enrichment |
| `agents/resolution/` | API Workflow trigger | Called by Maestro when case hits Resolution |
| `agents/satisfaction/` | API Workflow trigger | Called after resolution approved |
| `IntakeBot/Main.xaml` | RPA Process | Pulls tickets, creates cases |
| `CaseOrchestrator/Main.xaml` | RPA Process | Drives case through all stages |
| `case_definition.json` | Maestro Case | Defines stages, fields, SLAs |

---

## Step-by-Step Setup (30 minutes)

### 1. Get Your Tenant (5 min)
- Go to https://www.uipath.com/developers/labs
- Fill the form, wait for email with credentials
- Log in to your Automation Cloud tenant

### 2. Set Up Maestro Case (10 min)
- Navigate to **Maestro** in the left sidebar
- Click **Cases** → **New Case Definition**
- Follow `uipath/maestro_case/setup_guide.md`
- Use `case_definition.json` as reference for fields/stages

### 3. Create the Triage Agent (5 min)
- Navigate to **Agent Builder**
- Click **Create Agent**
- Copy the system prompt from `agent_builder_config.json`
- Set output schema
- Connect to your Case Definition

### 4. Deploy the Python Backend (5 min)
- Option A: Run locally with `uvicorn orchestrator:app --port 8000`
- Option B: Deploy to Azure/Railway/Render (see docs/deployment.md)
- Note the URL — you'll need it for API Workflows

### 5. Create API Workflows (5 min)
- In Automation Cloud → **Automations** → **API Workflows**
- Create workflows matching `workflow_definitions.json`
- Point them to your deployed orchestrator URL
- Connect triggers to Maestro Case stage transitions

### 6. Import RPA Workflows (optional)
- Open UiPath Studio
- File → Open → select `IntakeBot/project.json`
- Publish to Orchestrator
- Schedule or trigger manually

---

## Testing the Full Flow

1. Create a test case manually in Maestro
2. Or trigger via API: `POST /cases/intake` with a test ticket
3. Watch it flow through stages in the Maestro dashboard
4. Check Action Center for human approval tasks
5. Verify satisfaction analysis runs after approval

---

## Key Concepts

- **Maestro Case** = The "brain" that tracks where each case is
- **Agent Builder** = Low-code AI agent that runs inside UiPath
- **API Workflows** = REST endpoints that UiPath exposes/calls
- **Action Center** = Where humans approve/reject agent decisions
- **Orchestrator** = Manages RPA bots, queues, and scheduling

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent not triggering | Check stage transition is connected to API Workflow |
| API Workflow timeout | Increase timeout in HTTP connector settings |
| Action Center task not appearing | Verify `requires_human_approval` is true |
| Case stuck in stage | Check SLA rules and transition conditions |
