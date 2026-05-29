# Intelligent Customer Escalation Management
## UiPath AgentHack 2025 — Track 1: Maestro Case

---

## The Problem

- Customer support teams lose **hours** on manual triage, context-gathering, and routing
- High-value customers churn because complex issues bounce between departments
- Escalations requiring judgment get stuck in queues alongside routine tickets
- **Result:** Slow resolution, lost revenue, poor customer experience

---

## Our Solution

An **agentic case management system** that orchestrates AI agents, RPA bots, and human decision-makers to handle complex customer escalations — from intake to resolution.

```
INTAKE → TRIAGE → ROUTING → RESOLUTION → SATISFACTION CHECK
  │         │         │           │              │
[RPA]   [AI Agent] [AI Agent] [Human+Agent]  [AI Agent]
```

---

## Why Maestro Case (Track 1)?

Dynamic, unpredictable paths that emerge as work unfolds:

| Trigger | Dynamic Branch |
|---------|---------------|
| VIP customer detected | Skip queue, assign dedicated agent |
| Legal threat mentioned | Route to legal + compliance flag |
| Sentiment drops mid-case | Auto-escalate to senior agent |
| Customer unresponsive 48h | Auto-follow-up then close |
| Social media virality | Trigger PR crisis protocol |

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
         │ API Workflow │
         └──────┬──────┘
                │
   ┌────────────┼─────────────────┐
   ▼            ▼                 ▼
┌────────┐ ┌───────────┐ ┌──────────────┐
│Context │ │Resolution │ │Satisfaction  │
│ Agent  │ │  Agent    │ │   Agent      │
│LangChain│ │LangChain │ │  CrewAI      │
└────────┘ └───────────┘ └──────────────┘
```

---

## UiPath Components Used

| Component | Purpose |
|-----------|---------|
| **Maestro Case** | Case lifecycle, stage transitions, SLA enforcement |
| **Agent Builder** | Triage Agent (native low-code) |
| **API Workflows** | REST endpoints for external agents |
| **RPA (Studio)** | Intake bots — email, chat, social media |
| **Action Center** | Human-in-the-loop approvals |
| **Orchestrator** | Queue management, scheduling |

---

## AI Agents

| Agent | Framework | LLM | Role |
|-------|-----------|-----|------|
| Triage | UiPath Agent Builder | GPT-4o | Classifies urgency, detects intent |
| Context | LangChain (Python) | Claude 3.5 | Enriches case with CRM data |
| Resolution | LangChain (Python) | GPT-4o | Drafts responses, suggests actions |
| Satisfaction | CrewAI (Python) | GPT-4o-mini | Post-resolution analysis, churn prediction |

---

## Coding Agents (Bonus Points)

Built using **UiPath for Coding Agents**:

- **Claude Code** — Generated LangChain agent logic, FastAPI services, test cases
- **Cursor** — Iterated on agent prompts and workflow definitions

*Demo video includes walkthrough of coding agent usage*

---

## Live Demo

1. Ticket arrives via email → RPA bot ingests
2. Triage Agent classifies urgency & sentiment
3. Context Agent enriches with CRM data (VIP detected!)
4. Resolution Agent drafts response + compensation
5. Human approves in Action Center
6. Satisfaction Agent monitors post-resolution feedback

---

## Business Impact

- **70% reduction** in average triage time
- **3x faster** context gathering (automated CRM lookup)
- **Zero missed** VIP escalations
- **SLA compliance** tracked automatically via Maestro Case
- **Scalable** — handles 10x ticket volume without additional headcount

---

## Tech Stack

- **Orchestration:** UiPath Maestro Case + Orchestrator + Action Center
- **Native Agent:** UiPath Agent Builder
- **External Agents:** Python 3.11 + LangChain + CrewAI
- **LLMs:** OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Infrastructure:** Docker, FastAPI
- **Coding Agents:** Claude Code, Cursor

---

## Thank You

**GitHub:** [github.com/your-username/uipath-agenthack](https://github.com/your-username/uipath-agenthack)

**Track:** UiPath Maestro Case (Track 1)

**License:** MIT
