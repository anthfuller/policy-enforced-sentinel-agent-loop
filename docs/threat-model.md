# Threat Model

## Assumption

The agent is not trusted as a security boundary.

The model may reason incorrectly, follow malicious instructions, hallucinate tool usage, or attempt to provide unauthorized parameters.

## Threats and controls

| Threat | Control |
|---|---|
| Agent-generated KQL | Child workflow uses fixed KQL only |
| Agent-selected workspace | Workspace is fixed in workflow and validated by PEP |
| Prompt injection | PEP validates fixed contract outside the model |
| Secret exfiltration | No secrets or keys are stored in the workflow |
| Unauthorized tool call | Tool execution mediated by child workflow and PEP |
| Direct PEP bypass | PEP protected by Entra ID and private endpoint |
| Broad Sentinel access | Managed identity + RBAC scope |
| Public exposure | VNet integration and Private Endpoints |
| Malformed request | PEP deny response and fail-closed workflow path |
| Overly broad tool surface | One narrow approved tool per child workflow |
| Audit gap | PEP decision ID, workflow run ID, and Log Analytics audit validation |

## Non-goals

This Stage 1 implementation does not attempt to:

- Create a general Sentinel agent
- Allow arbitrary KQL
- Allow arbitrary workspace selection
- Execute incident changes directly
- Replace Sentinel RBAC
- Replace SOC approval workflows

Future tools should add explicit approvals and stronger policy for write actions such as incident creation.
