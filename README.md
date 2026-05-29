# Intelligent Customer Escalation Management

An agentic case management solution built on UiPath Maestro Case that orchestrates AI agents, RPA bots, and human decision-makers to handle complex customer escalations — from intake to resolution.

**Track:** UiPath Maestro Case (Track 1)  
**Hackathon:** UiPath AgentHack 2025

---

## Problem Statement

Customer support teams lose hours on manual triage, context-gathering, and routing. High-value customers churn because complex issues bounce between departments with no coordination. Escalations that require judgment get stuck in queues alongside routine tickets.

This solution uses agentic AI to automate the predictable parts (triage, enrichment, drafting) while keeping humans in control of sensitive decisions (legal threats, VIP retention, compensation approval).

---

## Solution Overview

A Maestro Case orchestrates the full lifecycle of a customer escalation:

```
INTAKE → TRIAGE → ROUTING → RESOLUTION → SATISFACTION CHECK
  │         │         │           │              │
[RPA]   [AI Agent] [AI Agent] [Human+Agent]  [AI Agent]
```

### Dynamic Paths (Why Maestro Case)

- VIP customer detected → skip queue, assign dedicated agent
- Legal threat mentioned → route to legal + compliance flag
- Sentiment drops mid-case → auto-escalate to senior agent
- Customer unresponsive 48h → auto-follow-up then close
- Resolution rejected → re-open and escalate tier
- Social media virality → trigger PR crisis protocol

---

## Architecture

```
                UiPath Automation Cloud
         ┌──────────────────────────────────┐
         │         Maestro Case              │
         │   (case lifecycle + SLA tracking) │
         └──────┬───────────────┬───────────┘
                │               │
   ┌────────────▼──┐     ┌─────▼────────────┐
   │  UiPath RPA   │     │  Action Center    │
   │ (intake bots) │     │ (human approvals) │
   └────────────┬──┘     └──────────────────┘
                │
         ┌──────▼──────┐
         │ API Workflow │ (REST endpoints)
         └──────┬──────┘
                │
   ┌────────────┼─────────────────┐
   ▼            ▼                 ▼
┌────────┐ ┌───────────┐ ┌──────────────┐
│Context │ │Resolution │ │Satisfaction  │
│ Agent  │ │  Agent    │ │   Agent      │
│LangChain│ │LangChain │ │  CrewAI      │
│Python  │ │  Python   │ │  Python      │
└────────┘ └───────────┘ └──────────────┘
```

---

## UiPath Components Used

| Component | Purpose |
|-----------|---------|
| **Maestro Case** | Case lifecycle management, stage transitions, SLA enforcement |
| **Agent Builder** | Triage Agent (native low-code agent) |
| **API Workflows** | REST endpoints for external agents to update cases |
| **RPA (Studio)** | Intake bots pulling from email, chat, social media |
| **Action Center** | Human-in-the-loop approvals for sensitive decisions |
| **Orchestrator** | Queue management, scheduling, monitoring |

---

## External Agents & Frameworks

| Agent | Framework | LLM | Role |
|-------|-----------|-----|------|
| Triage Agent | UiPath Agent Builder | GPT-4o | Classifies urgency, detects intent & sentiment |
| Context Agent | LangChain (Python) | Claude 3.5 Sonnet | Enriches case with customer history from CRM |
| Resolution Agent | LangChain (Python) | GPT-4o | Drafts responses, suggests actions & compensation |
| Satisfaction Agent | CrewAI (Python) | GPT-4o-mini | Analyzes post-resolution feedback, predicts churn |

---

## Coding Agents Used (Bonus)

This solution was built using **UiPath for Coding Agents**:

- **Claude Code** — Generated LangChain agent logic, FastAPI services, and test cases
- **Cursor** — Used for iterating on agent prompts and workflow definitions

The demo video includes a walkthrough of how coding agents were used during development.

---

## Tech Stack

- **Orchestration:** UiPath Maestro Case + Orchestrator + Action Center
- **Native Agent:** UiPath Agent Builder (Triage)
- **External Agents:** Python 3.11 + LangChain 0.2 + CrewAI 0.5
- **LLMs:** OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Mock Services:** FastAPI (CRM simulator, ticket generator)
- **Coding Agents:** Claude Code, Cursor

---

## Project Structure

```
uipath-agenthack/
├── agents/
│   ├── triage/          # UiPath Agent Builder config
│   ├── context/         # LangChain - CRM enrichment agent
│   ├── resolution/      # LangChain - response drafting agent
│   └── satisfaction/    # CrewAI - post-resolution analysis
├── services/
│   ├── mock_crm/        # FastAPI - customer data simulator
│   └── mock_tickets/    # FastAPI - inbound ticket simulator
├── uipath/
│   ├── workflows/       # RPA intake workflows
│   └── api_workflows/   # API Workflow definitions
├── config/              # Environment configs, case schema, prompts
├── tests/               # Agent and integration tests
├── docs/                # Architecture diagrams, presentation
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Prerequisites

- Python 3.11+
- UiPath Automation Cloud account (via UiPath Labs)
- OpenAI API key
- Anthropic API key

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/uipath-agenthack.git
cd uipath-agenthack
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### 4. Start mock services

```bash
# Terminal 1 - CRM service
uvicorn services.mock_crm.main:app --port 8001

# Terminal 2 - Ticket service
uvicorn services.mock_tickets.main:app --port 8002
```

### 5. Run agents locally (for testing)

```bash
python -m agents.context.agent
python -m agents.resolution.agent
python -m agents.satisfaction.agent
```

### 6. Deploy to UiPath Automation Cloud

Follow the UiPath deployment guide in `docs/deployment.md`.

---

## Demo Video

[Link to 5-minute demo video] *(to be added before submission)*

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
