# Policy-Enforced Sentinel Agent Loop

A private-by-design reference pattern for governed Microsoft Sentinel automation using Azure Logic Apps Standard Agent Loop, a controlled child workflow tool boundary, an Azure Function-based Policy Enforcement Point (PEP), Entra ID / App Service Authentication, managed identity, RBAC, VNet integration, Private Endpoints, and private DNS.

The goal is not to build an unrestricted AI agent.

The goal is to prove a security control pattern:

```text
Agent Loop request
  → approved tool call
  → Logic Apps Standard child workflow boundary
  → Azure Function-based PEP
  → Entra ID-authenticated allow/deny decision
  → fixed approved Sentinel query only
  → return result or fail closed
```

## Status

Stage 1 reference implementation is complete for the Sentinel Health Query Tool. Additional governed child workflow tools, including SOC notification and incident-oriented tools, should be added incrementally using the same policy-enforced child workflow pattern.

This repository documents the control pattern. It is not a one-click production deployment package.


## Why this exists

Agentic SOC workflows are useful, but the model should not directly execute security actions.

This pattern treats agent output as untrusted for execution decisions:

- The agent cannot generate KQL.
- The agent cannot choose the workspace.
- The agent cannot choose a query ID.
- The agent cannot supply credentials, endpoints, tokens, or secrets.
- The agent cannot call Sentinel directly.
- The child workflow calls the PEP before any Sentinel action.
- The Sentinel query action exists only in the allow branch.
- Denied, malformed, failed, or unauthorized requests fail closed.

## What was validated

The hardened reference flow validates that:

- The parent Agent Loop can call the controlled child workflow.
- The child workflow calls the PEP before Sentinel execution.
- The PEP Function App is protected by Entra ID / App Service Authentication.
- The Logic App calls the PEP with managed identity.
- EasyAuth restricts access to a specific client application, specific managed identity, and issuer tenant.
- The PEP code validates caller claims including `appid`, `tid`, and `aud`.
- Only a fixed, approved Sentinel health query can execute after an allow decision.
- The child workflow returns success or denial back to the Agent Loop.

## Stage 1 reference implementation

This repository starts with one governed tool:

```text
Sentinel Health Query Tool
```

This tool performs one fixed Sentinel health query through the Azure Monitor Logs connector after PEP approval.

Planned future governed tools:

- Sentinel Change Auditing Tool
- Sentinel Engineering Ticket Tool
- Sentinel Incident Creation Tool
- Notification / Email Tool

Each tool should follow the same enforcement model.

## Private-by-design model

This pattern assumes a private Azure environment:

- Logic App Standard uses VNet integration for outbound calls.
- Logic App Standard can use private inbound access where required.
- PEP Function App is private and protected by Entra ID / App Service Authentication.
- Supporting services use Private Endpoints.
- Private DNS zones map Azure service hostnames to private IPs.
- A private jump box can be used for administrative validation.
- Azure Monitor / Log Analytics can be restricted through Azure Monitor Private Link Scope where required.
- Managed identity and RBAC are used instead of embedded credentials.

No Function keys.  
No API keys.  
No client secrets.  
No shared secrets.  
No Log Analytics shared keys.  
No public inbound exposure for the secured workflow path.  
No agent-generated KQL.  
No agent-selected workspace.

## Repository contents

```text
.github/
  PULL_REQUEST_TEMPLATE.md

docs/
  architecture.md
  deployment-runbook.md
  identity-rbac-model.md
  networking-private-design.md
  security-design.md
  threat-model.md
  sanitization-checklist.md
  linkedin-post.md

diagrams/
  architecture.mmd
  sequence-flow.mmd
  fail-closed-flow.mmd

src/pep_function/
  function_app.py
  local.settings.example.json
  requirements.txt

workflows/
  parent-agent-loop-sanitized.json
  child-sentinel-health-query-tool-sanitized.json

samples/
  pep-request-allow.json
  pep-response-allow.json
  pep-request-deny-forbidden-kql.json
  audit-validation-query.kql

tools/
  sanitize_check.py

README.md
LICENSE
NOTICE.md
.gitignore
```

## Important authentication note

The Azure Function uses:

```python
func.AuthLevel.ANONYMOUS
```

This is intentional in this design.

Authentication is enforced by Azure App Service Authentication / EasyAuth at the platform layer. The function then validates EasyAuth caller claims in code and acts as the Policy Enforcement Point.

Before publishing or deploying, ensure the Function App Authentication provider is configured to:

- Require authentication.
- Return HTTP 401 for unauthenticated requests.
- Allow requests only from the expected issuer tenant.
- Allow requests only from the specific Logic App managed identity client application.
- Allow requests only from the specific managed identity object/principal ID.
- Use the expected token audience: `api://<pep-app-registration-client-id>`.

## Quick validation model

Expected parent path:

```text
HTTP request received
  → Agent Loop runs
  → Sentinel Health Query tool selected
  → Call workflow in this logic app succeeded
```

Expected child path:

```text
HTTP request received
  → Correlation ID initialized
  → PEP called
  → PEP response parsed
  → PEP allow condition true
  → Fixed Azure Monitor Logs query succeeded
  → Success response returned
```

Expected Function log proof:

```text
PEP decision: allow=True reason=PEP allow: fixed Sentinel health query is authorized decisionId=<guid>
Executed 'Functions.pep_evaluate' (Succeeded)
```

Expected audit proof:

```kql
LAQueryLogs
| where TimeGenerated > ago(60m)
| where QueryText has "SecurityIncident"
| project TimeGenerated, AADObjectId, AADClientId, RequestClientApp, ResponseCode, QueryText
| order by TimeGenerated desc
```

Expected values:

```text
RequestClientApp = AzureMonitorLogsConnector
ResponseCode = 200
AADObjectId = managed identity used by the Azure Monitor Logs connector
```

## Design principle

The interesting part is not that an agent can query Sentinel.

The interesting part is proving that the agent cannot query Sentinel unless the request passes identity validation, platform authentication, policy enforcement, an approved tool path, the approved workspace, and the fixed authorized query.

## License

Apache License 2.0. See [LICENSE](LICENSE).
