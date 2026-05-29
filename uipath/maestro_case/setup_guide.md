# Maestro Case Setup Guide

## Overview

This guide walks you through setting up the **Customer Escalation** case definition in UiPath Maestro Case on Automation Cloud.

---

## Step 1: Create the Case Definition

1. Log in to **UiPath Automation Cloud** → Navigate to **Maestro**
2. Click **Cases** → **Create Case Definition**
3. Enter:
   - Name: `Customer Escalation`
   - Prefix: `ESC`
   - Description: `Manages complex customer escalations from intake to resolution`

---

## Step 2: Define Stages

Create the following stages in order:

| # | Stage | SLA | Actor |
|---|-------|-----|-------|
| 1 | Intake | 1h | RPA Bot |
| 2 | Triage | 2h | Triage Agent (Agent Builder) |
| 3 | Enrichment | 4h | Context Agent (API Workflow) |
| 4 | Resolution | 24h | Resolution Agent + Human |
| 5 | Satisfaction | 48h | Satisfaction Agent (API Workflow) |
| 6 | Closed | — | System |

For each stage:
- Set the SLA duration
- Configure the exit criteria (see `case_definition.json`)
- Set auto-transition where applicable

---

## Step 3: Define Case Fields

In the case definition, add these field groups:

### Customer Fields
- `customer_id` (Text, Required)
- `customer_name` (Text)
- `customer_tier` (Choice: standard/premium/gold/platinum/enterprise/vip, Required)
- `lifetime_value` (Number)
- `churn_risk_score` (Number, 0-1)

### Ticket Fields
- `ticket_id` (Text, Required)
- `source` (Choice: email/chat/phone/social_media/portal, Required)
- `subject` (Text, Required)
- `body` (Long Text, Required)

### Triage Fields
- `urgency_score` (Number, 0-1)
- `sentiment_score` (Number, -1 to 1)
- `category` (Choice: billing/technical/account/complaint/legal/general)
- `intent` (Text)
- `flags` (Multi-select: legal_threat/vip_customer/social_media_public/churn_risk)
- `recommended_team` (Text)

### Resolution Fields
- `draft_response` (Long Text)
- `suggested_actions` (Multi-line Text)
- `compensation` (Text)
- `requires_human_approval` (Yes/No)
- `approved_by` (Text)

### Satisfaction Fields
- `satisfaction_score` (Number, 0-1)
- `churn_probability` (Number, 0-1)
- `follow_up_required` (Yes/No)

---

## Step 4: Configure Transitions

Set up stage transitions:

```
Intake → Triage          (Auto: when ticket ingested)
Triage → Enrichment      (Auto: when urgency scored)
Enrichment → Resolution  (Auto: when context brief generated)
Resolution → Satisfaction (Manual: human approves OR auto-resolved)
Satisfaction → Closed    (Auto: satisfaction > 0.5 AND churn < 0.5)
Satisfaction → Resolution (Auto: re-escalate if satisfaction <= 0.3)
```

---

## Step 5: Configure Dynamic Paths

These are the exception-handling rules that make this Track 1 (not Track 2):

1. **VIP Fast Track**: If `customer_tier` is VIP/Enterprise → skip queue
2. **Legal Escalation**: If `flags` contains "legal_threat" → route to legal
3. **Sentiment Drop**: If `sentiment_score < -0.7` → escalate to senior
4. **Social Media Crisis**: If `flags` contains "social_media_viral" → PR protocol
5. **Unresponsive Customer**: If no response in 48h → auto-follow-up
6. **Resolution Rejected**: If human rejects → re-escalate tier

---

## Step 6: Configure Action Center Tasks

Create these human-in-the-loop tasks:

### Task 1: Approve Resolution
- Trigger: `requires_human_approval == true`
- Assigned to: `recommended_team`
- Actions: Approve / Reject / Modify & Approve
- SLA: 4 hours

### Task 2: Legal Review
- Trigger: `flags` contains "legal_threat"
- Assigned to: Legal Team
- Actions: Approve / Reject / Escalate External
- SLA: 2 hours

### Task 3: VIP Retention Decision
- Trigger: VIP/Enterprise customer AND `churn_risk_score > 0.6`
- Assigned to: Account Manager
- Actions: Approve / Increase Compensation / Schedule Call
- SLA: 2 hours

---

## Step 7: Connect API Workflows

Create API Workflows that our Python agents can call:

| Endpoint | Purpose | Triggers |
|----------|---------|----------|
| `POST /cases/{id}/triage` | Receives triage results | Triage Agent |
| `POST /cases/{id}/enrich` | Receives context brief | Context Agent |
| `POST /cases/{id}/resolve` | Receives resolution draft | Resolution Agent |
| `POST /cases/{id}/satisfaction` | Receives satisfaction analysis | Satisfaction Agent |

See `uipath/api_workflows/README.md` for endpoint specifications.

---

## Step 8: Connect Agent Builder

1. Go to **Agent Builder** → Create new agent
2. Name: `Escalation Triage Agent`
3. Paste the system prompt from `agents/triage/agent.py` (the `TRIAGE_SYSTEM_PROMPT`)
4. Configure output schema matching `TriageResult` model
5. Connect to the Maestro Case to auto-update triage fields

---

## Verification

After setup, test the flow:
1. Create a test case manually in Maestro
2. Verify it moves through stages
3. Check that Action Center tasks appear for approval
4. Confirm SLA timers are running
