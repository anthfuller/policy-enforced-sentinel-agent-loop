# Deployment Runbook

## 1. Prepare Logic App Standard

Use one Logic App Standard resource to host:

```text
Parent workflow: <parent-agent-workflow-name>
Child workflow: <child-workflow-name>
```

## 2. Build child workflow first

Create a regular stateful workflow.

Recommended action order:

> **Triggering model**
>
> The child workflow is request-triggered and acts as the controlled tool boundary.  
> A parent workflow can invoke the child through an HTTP request, an Agent Loop tool call, a Recurrence-triggered schedule, or another approved orchestration path.
>
> In a scheduled design, the Recurrence trigger belongs in the parent workflow. The child workflow remains the governed callable tool.

```text
When an HTTP request is received
Initialize CorrelationId
Call PEP
Parse PEP Response
Condition PEP Allows
  True branch:
    Run Sentinel Health Query
    Return Success To Agent Loop
  False branch:
    Return Denial To Agent Loop
Return PEP Failure Denial To Agent Loop
```

The child workflow is the controlled tool boundary.

## 3. Configure PEP call

HTTP action:

```text
Action name: Call PEP
Method: POST
URI: https://<private-pep-function-fqdn>/api/pep_evaluate
Authentication: Managed Identity
Managed identity: <logic-app-pep-call-uami>
Audience: api://<pep-app-registration-client-id>
```

Body pattern:

```json
{
  "agentName": "SECURITY_AGENT_NAME_PLACEHOLDER",
  "toolName": "Sentinel Health Query",
  "operation": "sentinel.health.query",
  "workspace": "SENTINEL_WORKSPACE_ALIAS_PLACEHOLDER",
  "queryId": "sentinel_health_query_weekly_v1",
  "inputs": {},
  "logicAppRunId": "@{workflow().run.name}",
  "correlationId": "@{variables('correlationId')}"
}
```

## 3a. Configure Function App Authentication

Function App → Authentication → Microsoft provider:

```text
App Service authentication: Enabled
Unauthenticated requests: Return HTTP 401
Application client ID: <pep-app-registration-client-id>
Issuer URL: https://login.microsoftonline.com/<tenant-id>
Allowed token audience: api://<pep-app-registration-client-id>
Client application requirement: Allow requests from specific client applications
Allowed client applications: <logic-app-managed-identity-client-id>
Identity requirement: Allow requests from specific identities
Allowed identities: <logic-app-managed-identity-object-or-principal-id>
Tenant requirement: Allow requests only from the issuer tenant
```

The Function App code also validates EasyAuth claims before evaluating the tool contract.

## 4. PEP allow condition

Require all of the following:

```text
PEP HTTP status code == 200
allow == boolean true
toolName == Sentinel Health Query
operation == sentinel.health.query
workspace == SENTINEL_WORKSPACE_ALIAS_PLACEHOLDER
queryId == sentinel_health_query_weekly_v1
```

Do not place Sentinel execution before this condition.

## 5. Azure Monitor Logs action

Inside the true branch only:

```text
Connector: Azure Monitor Logs
Operation: Run query and list results
Authentication: Managed Identity
Managed identity: system-assigned managed identity
Resource type: Log Analytics Workspace
Workspace: <sentinel-log-analytics-workspace-name>
Resource group: <workspace-resource-group>
Time range: Set in query
```

Important:

```text
Use the resource group that contains the Log Analytics workspace.
Do not assume it is the same resource group as the Logic App.
```

Fixed KQL only:

```kql
SecurityIncident
| where TimeGenerated >= ago(24h)
| project TimeGenerated, IncidentNumber, Title, Severity, Status, Owner, Classification, Description
| order by TimeGenerated desc
| take 25
```

Do not use dynamic content for:

```text
KQL
workspace
resource group
queryId
subscription
endpoint
credentials
```

## 6. Parent Agent Loop workflow

Parent flow:

```text
When an HTTP request is received
  → Agent Loop
  → Tool: Sentinel Health Query
  → Workflow Operations: Call workflow in this logic app
  → Child workflow: <child-workflow-name>
```

Do not call the child workflow using the HTTP callback URL.

## 7. Parent agent instructions

Example:

```text
You are a Microsoft Sentinel security operations agent.
You do not execute Sentinel actions directly.
You may only use the approved Sentinel Health Query tool.
You must not generate KQL.
You must not choose a workspace.
You must not choose a queryId.
You must not invent tools, credentials, URLs, endpoints, workspaces, or actions.
All execution must go through the provided tool, which calls an external Policy Enforcement Point before any approved action is allowed.
If the request is outside the available tool capability, say it is not available.
```

## 8. Parent-to-child mapping

Pass only safe metadata:

```json
{
  "correlationId": "@{workflow().run.name}",
  "callerWorkflow": "<parent-agent-workflow-name>",
  "requestReason": "Sentinel health check requested by parent agent."
}
```

Do not pass:

```text
KQL
workspace
resource group
subscription
queryId
endpoint
token
secret
key
connection string
```

## 9. Validation

Parent run history:

```text
HTTP request received = succeeded
Agent Loop = succeeded
Tool selected = succeeded
Call workflow in this logic app = succeeded
```

Child run history:

```text
HTTP request received = succeeded
Initialize CorrelationId = succeeded
Call PEP = succeeded
Parse PEP Response = succeeded
Condition PEP Allows = true
Run Sentinel Health Query = succeeded
Return Success To Agent Loop = succeeded
```

Audit validation:

```kql
LAQueryLogs
| where TimeGenerated > ago(60m)
| where QueryText has "SecurityIncident"
| project TimeGenerated, AADObjectId, AADClientId, RequestClientApp, ResponseCode, QueryText
| order by TimeGenerated desc
```
