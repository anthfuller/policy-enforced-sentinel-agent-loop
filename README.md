# Policy-Enforced Sentinel Agent Loop

A private-by-design reference pattern for governed Microsoft Sentinel automation using an Azure Logic Apps Standard Agent Loop, a controlled child-workflow tool boundary, and an Azure Function-based Policy Enforcement Point (PEP).

This repository demonstrates an **architectural security control pattern**. It is **not intended to be deployed directly into production** without independent security review and adaptation to your environment.

## Status

Stage 1 reference implementation is complete for the **Sentinel Health Query Tool**. Additional governed child workflow tools are planned.

## Architecture note

This repository documents the control pattern, not a one-click deployment package.

The goal is **not** to build an unrestricted agent.
The goal is to prove a governance model:

```text
Agent Loop request
→ approved tool call
→ Logic Apps Standard child workflow boundary
→ Azure Function-based Policy Enforcement Point (PEP)
→ Entra ID-authenticated allow/deny decision
→ fixed, approved Sentinel query only
→ return result or fail closed
```

---

## Why this exists

Agentic SOC workflows are powerful, but models should not directly execute security actions.

This pattern treats the agent as **logically untrusted** for execution decisions:

- The agent cannot generate KQL.
- The agent cannot choose the Log Analytics workspace.
- The agent cannot choose a query ID.
- The agent cannot supply credentials, endpoints, tokens, or secrets.
- The agent cannot call Microsoft Sentinel directly.
- A child workflow calls the PEP before any Sentinel action.
- The Sentinel query action exists only within the allow branch.
- Denied, malformed, or unauthorized requests **fail closed**.

---

## Stage 1 reference implementation

This repository starts with one governed tool:

**Sentinel Health Query Tool**  
Performs a single, fixed Sentinel health query through the Azure Monitor Logs connector after PEP approval.

Planned future governed tools:

- Sentinel Change Auditing Tool
- Sentinel Engineering Ticket Tool
- Sentinel Incident Creation Tool
- Notification or Email Tool

All future tools follow the same enforcement model.

---

## Private-by-design model

This pattern assumes a private Azure deployment:

- Logic Apps Standard uses private inbound access where required.
- Logic Apps Standard uses VNet integration for outbound calls.
- The PEP Function App is private and protected by Entra ID App Service Authentication.
- Supporting services use Private Endpoints.
- Azure Monitor / Log Analytics may be restricted using Azure Monitor Private Link Scope.
- Private DNS zones map Azure service hostnames to private IP addresses.
- Managed identity and RBAC are used instead of embedded credentials.

No Function keys.  
No API keys.  
No client secrets.  
No shared secrets.  
No Log Analytics shared keys.  
No public inbound exposure for protected workflow paths in the private deployment model.

---

## Repository contents

```text
/docs
  architecture.md
  deployment-runbook.md
  identity-rbac-model.md
  networking-private-design.md
  security-design.md
  threat-model.md
  sanitization-checklist.md
  linkedin-post.md

/diagrams
  architecture.mmd
  sequence-flow.mmd
  fail-closed-flow.mmd

/src/pep_function
  function_app.py
  local.settings.example.json
  requirements.txt

/workflows
  parent-agent-loop-sanitized.json
  child-sentinel-health-query-tool-sanitized.json

/samples
  pep-request-allow.json
  pep-response-allow.json
  pep-request-deny-forbidden-kql.json
  audit-validation-query.kql

/tools
  sanitize_check.py
```

---

## Public repository sanitization requirements

This repository is intentionally published as a **sanitized reference implementation**.

**Do not commit real, environment-specific, or identifying values.**
All examples must remain generic and non-attributable.

The following **must never appear** in this repository.

### Identifiers

- Subscription IDs
- Tenant IDs
- Client IDs or Application IDs
- Object IDs
- Managed identity names

### Environment details

- Resource group names
- Workspace names
- Private endpoint names
- Private DNS zone names
- Private FQDNs
- Callback URLs or webhook URLs

### Security-sensitive data

- Keys, tokens, secrets, or certificates
- Log Analytics shared keys
- Function keys
- Authorization headers

### Operational or customer data

- Sentinel incident data
- Alert payloads from real environments
- Run history screenshots containing URLs or identifiers
- Customer names or internal project names

Use placeholders only, for example:

```text
<SUBSCRIPTION_ID>
<TENANT_ID>
<WORKSPACE_NAME>
<RESOURCE_GROUP_NAME>
<PEP_FUNCTION_PRIVATE_FQDN>
<MANAGED_IDENTITY_NAME>
```

Replace placeholders only within a private environment.

---

## Quick validation model

**Expected parent path:**

```text
HTTP request received
→ Agent Loop runs
→ Sentinel Health Query Tool selected
→ Child workflow call succeeds
```

**Expected child path:**

```text
HTTP request received
→ Correlation ID initialized
→ PEP called
→ PEP response parsed
→ Allow decision validated
→ Fixed Azure Monitor Logs query executes
→ Success response returned
```

**Expected audit proof:**

Example Log Analytics validation query:

```kusto
LAQueryLogs
| where TimeGenerated > ago(60m)
| where QueryText has "SecurityIncident"
| project TimeGenerated, AADObjectId, AADClientId, RequestClientApp, ResponseCode, QueryText
| order by TimeGenerated desc
```

Expected values:

- `RequestClientApp = AzureMonitorLogsConnector`
- `ResponseCode = 200`

---

## Design principle

The interesting part is not that an agent can query Sentinel.

The interesting part is proving that the agent **cannot** query Sentinel unless the request:

- Passes policy enforcement
- Uses an approved tool path
- Targets an approved workspace
- Executes only a fixed, authorized query

Fail closed by design.

---

## License

Apache License 2.0
