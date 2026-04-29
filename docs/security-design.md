# Security Design

## Core security rules

- The agent does not execute Sentinel actions directly.
- The agent does not generate KQL.
- The agent does not choose a workspace.
- The agent does not choose a query ID.
- The agent does not pass credentials, secrets, endpoints, tokens, or connection strings.
- The child workflow calls the PEP before Sentinel execution.
- The Azure Monitor Logs query is only in the PEP allow branch.
- Deny, malformed JSON, unauthorized caller, failed PEP, failed condition, timeout, or skipped condition fails closed.

## Credential model

This pattern uses:

- Entra ID authentication
- Azure App Service Authentication / EasyAuth
- Managed identity
- Azure RBAC

This pattern avoids:

- Function keys
- API keys
- Client secrets
- Shared secrets
- Log Analytics shared keys
- Embedded tokens

## Platform authentication controls

The PEP Function App should be protected with Microsoft identity provider / EasyAuth:

| Control | Required setting |
|---|---|
| App Service authentication | Enabled |
| Unauthenticated requests | Return HTTP 401 |
| Client application requirement | Allow requests from specific client applications |
| Allowed client application | Logic App managed identity client ID |
| Identity requirement | Allow requests from specific identities |
| Allowed identity | Logic App managed identity object/principal ID |
| Tenant requirement | Allow requests only from the issuer tenant |
| Allowed token audience | `api://<pep-app-registration-client-id>` |

## Function auth level

The Python Azure Function uses:

```python
func.AuthLevel.ANONYMOUS
```

This is intentional only when EasyAuth is enabled and required at the platform layer.

The security boundary is not the Azure Functions key model. The security boundary is:

1. EasyAuth enforcing Entra ID authentication before the function runs.
2. Specific client application restriction.
3. Specific managed identity restriction.
4. Tenant restriction.
5. PEP code validating EasyAuth claims.
6. Fixed tool contract enforcement.
7. Fail-closed workflow branching.

## PEP claim validation

The PEP validates EasyAuth caller claims:

| Claim | Purpose |
|---|---|
| `appid` / `azp` / `client_id` | Confirms the calling managed identity client application |
| `tid` | Confirms the expected tenant |
| `aud` | Confirms the token audience is the PEP API |

If validation fails, the PEP returns HTTP 401 and no Sentinel action executes.

## Fixed tool contract

The PEP validates a narrow tool contract.

Example contract fields:

```json
{
  "agentName": "SECURITY_AGENT_NAME_PLACEHOLDER",
  "toolName": "Sentinel Health Query",
  "operation": "sentinel.health.query",
  "workspace": "SENTINEL_WORKSPACE_ALIAS_PLACEHOLDER",
  "queryId": "sentinel_health_query_weekly_v1",
  "inputs": {}
}
```

Forbidden fields include:

```text
kql
queryText
workspaceId
resourceId
uri
url
endpoint
apiKey
functionKey
clientSecret
sharedKey
connectionString
token
secret
```

## Fail-closed behavior

The child workflow should return denial if:

- PEP returns `allow: false`
- PEP response is malformed
- PEP call fails
- PEP call times out
- PEP condition fails
- Required contract values do not match
- Request includes forbidden fields
- Caller identity validation fails

Nothing Sentinel-related should run before the PEP condition, in the deny branch, or after a failed condition.
