# Deployment Guide

## Local Development

### 1. Start Mock Services

```bash
# Terminal 1
uvicorn services.mock_crm.main:app --port 8001 --reload

# Terminal 2
uvicorn services.mock_tickets.main:app --port 8002 --reload
```

### 2. Start the Orchestrator

```bash
# Terminal 3
uvicorn orchestrator:app --port 8000 --reload
```

### 3. Test the Flow

```bash
# Create a case
curl -X POST http://localhost:8000/cases/intake \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-1001",
    "customer_id": "CUST-001",
    "source": "email",
    "subject": "API response times unacceptable",
    "body": "Our integration has been experiencing 5-10 second response times.",
    "customer_tier": "vip"
  }'

# Triage the case (replace CASE-ID with actual ID from above)
curl -X POST http://localhost:8000/cases/CASE-ID/triage

# Enrich with context
curl -X POST http://localhost:8000/cases/CASE-ID/enrich

# Generate resolution
curl -X POST http://localhost:8000/cases/CASE-ID/resolve

# Approve resolution
curl -X POST http://localhost:8000/cases/CASE-ID/human-decision \
  -H "Content-Type: application/json" \
  -d '{"case_id": "CASE-ID", "approved": true, "notes": "Looks good"}'

# Check satisfaction
curl -X POST http://localhost:8000/cases/CASE-ID/satisfaction

# Close case
curl -X POST http://localhost:8000/cases/CASE-ID/close
```

---

## UiPath Automation Cloud Deployment

### Prerequisites
- UiPath Automation Cloud tenant (via UiPath Labs)
- Maestro Case enabled
- Agent Builder access
- Action Center configured

### Step 1: Deploy Python Orchestrator

Option A: Deploy to a cloud VM (AWS EC2, Azure VM, etc.)
Option B: Deploy as a Docker container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Configure UiPath API Workflows

1. In Orchestrator, create API Workflow connections pointing to your deployed orchestrator URL
2. Configure authentication (API key header)
3. Map each endpoint to a workflow trigger

### Step 3: Set Up Maestro Case

1. Create a Case Definition with stages: Intake → Triage → Routing → Resolution → Satisfaction → Closed
2. Configure stage transitions to trigger API Workflows
3. Set SLA rules (warning at 4h, breach at 8h)
4. Configure Action Center tasks for human approval stage

### Step 4: Configure Agent Builder (Triage Agent)

1. Create a new agent in Agent Builder
2. Use the triage prompt from `agents/triage/agent.py`
3. Connect to GPT-4o via AI Trust Layer
4. Map input/output to case fields

### Step 5: Set Up RPA Intake Bot

1. Create a UiPath Studio workflow that:
   - Monitors email inbox / chat queue / social media
   - Extracts ticket data
   - Calls `/cases/intake` endpoint
   - Logs to Orchestrator queue

### Step 6: Test End-to-End

1. Send a test ticket through the intake channel
2. Verify case progresses through all stages
3. Check Action Center for human approval task
4. Verify satisfaction analysis runs after resolution
