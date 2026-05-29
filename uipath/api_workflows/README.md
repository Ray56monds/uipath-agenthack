# UiPath API Workflow Definitions

This folder contains the API Workflow configurations that UiPath Orchestrator
uses to call the external Python agents.

## Endpoints Exposed to UiPath

| Endpoint | Method | Purpose | Called By |
|----------|--------|---------|-----------|
| `/cases/intake` | POST | Create new case from ticket | RPA Intake Bot |
| `/cases/{id}/triage` | POST | Run triage agent | Maestro Case (auto) |
| `/cases/{id}/enrich` | POST | Run context enrichment | Maestro Case (after triage) |
| `/cases/{id}/resolve` | POST | Generate resolution draft | Maestro Case (after routing) |
| `/cases/{id}/human-decision` | POST | Record human approval | Action Center callback |
| `/cases/{id}/satisfaction` | POST | Run satisfaction analysis | Maestro Case (after resolution) |
| `/cases/{id}/close` | POST | Close the case | Maestro Case / Human |
| `/cases/{id}` | GET | Get case details | Dashboard / Monitoring |

## UiPath Integration Pattern

```
Maestro Case (Stage Transition)
    → Triggers API Workflow
        → Calls Python orchestrator endpoint
            → Agent executes (LangChain/CrewAI)
                → Returns result to API Workflow
                    → Maestro Case updates stage
                        → If human needed → Action Center task created
```

## Deployment

The Python orchestrator runs as a containerized service (Docker) or on a VM.
UiPath API Workflows connect to it via HTTPS with API key authentication.

In production, deploy behind an API gateway with:
- Rate limiting
- API key validation
- Request logging
- Health checks
