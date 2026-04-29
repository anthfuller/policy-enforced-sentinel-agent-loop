# Architecture

## High-level flow

```text
Caller
  → Parent Agent Loop Workflow
  → Approved tool call
  → Child Workflow Tool Boundary
  → Azure Function-based PEP
  → Allow / Deny decision
      → Allow: fixed Azure Monitor Logs query
      → Deny: fail closed
  → Return response to Agent Loop
```

## Components

| Layer | Component | Purpose |
|---|---|---|
| Agent orchestration | Logic Apps Standard Agent Loop | Determines whether to call the approved tool |
| Tool boundary | Logic Apps Standard child workflow | Prevents direct agent execution of Sentinel actions |
| Policy enforcement | Azure Function-based PEP | Evaluates the fixed contract before execution |
| Identity | Entra ID + managed identity | Authenticates workflow-to-PEP and connector access |
| Data access | Azure Monitor Logs connector | Runs the fixed approved Sentinel query |
| Authorization | Azure RBAC | Grants the connector identity query access to the workspace |
| Network isolation | VNet integration + Private Endpoints | Keeps the workflow path private by design |

## Trust boundary

The agent is not trusted to enforce security.

The agent may request an action, but execution is mediated by:

1. Child workflow boundary
2. PEP contract validation
3. Managed identity authentication
4. RBAC
5. Fixed query placement
6. Fail-closed branching

## Stage 1 tool

```text
Sentinel Health Query Tool
```

The tool validates:

- agent name
- tool name
- operation
- workspace alias
- query ID
- absence of forbidden fields
- empty inputs

Then the child workflow runs one fixed Azure Monitor Logs query only if the PEP allows the request.
