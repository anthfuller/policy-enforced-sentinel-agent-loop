# Identity, Entra ID, and RBAC Model

## PEP protection

Use an Entra ID App Registration to protect the PEP Function App.

Placeholder values:

```text
App registration name: <pep-app-registration-name>
Application ID URI / allowed token audience: api://<pep-app-registration-client-id>
```

The Logic App HTTP action that calls the PEP uses:

```text
Authentication type: Managed Identity
Managed identity: <logic-app-pep-call-uami>
Audience: api://<pep-app-registration-client-id>
```

## EasyAuth hardening checklist

Configure the Function App Microsoft identity provider as follows:

```text
App Service authentication: Enabled
Unauthenticated requests: Return HTTP 401
Client application requirement: Allow requests from specific client applications
Allowed client applications: <logic-app-managed-identity-client-id>
Identity requirement: Allow requests from specific identities
Allowed identities: <logic-app-managed-identity-object-or-principal-id>
Tenant requirement: Allow requests only from the issuer tenant
Allowed token audiences: api://<pep-app-registration-client-id>
```

Important distinction:

```text
Client ID / Application ID = used for caller app validation and allowed client application.
Object ID / Principal ID = used for specific identity restriction.
```

## PEP code claim validation

The PEP also validates EasyAuth claims in code:

```text
appid / azp / client_id == expected Logic App managed identity client ID
tid == expected tenant ID
aud == expected PEP API audience
```

This creates defense in depth:

```text
Platform enforcement + PEP code validation + fixed tool contract
```

## Managed identity separation

Keep these identities separate where possible:

| Use | Recommended identity |
|---|---|
| Logic App call to PEP | User-assigned managed identity |
| Azure Monitor Logs connector | Logic App system-assigned managed identity or dedicated UAMI |

Do not mix the PEP call identity with the Azure Monitor Logs query identity unless your design explicitly requires it.

## Log Analytics RBAC

Grant RBAC at the Log Analytics workspace scope.

Recommended role:

```text
Log Analytics Data Reader
```

Acceptable for testing:

```text
Log Analytics Reader
```

Optional hardened model:

```text
Table-level RBAC for only the required Sentinel table
```

## API connection access policy

For the Azure Monitor Logs API connection, confirm the API connection access policy includes the same identity used by the connector.

Placeholder:

```text
Connection: <azure-monitor-logs-api-connection-name>
Authentication: Managed Identity
Managed identity: <logic-app-system-assigned-managed-identity>
```

## Client-safe diagram

```text
Parent Agent Workflow
        |
        | Internal tool call
        v
Child Workflow
        |
        | HTTP action using managed identity
        | Audience: api://<pep-app-registration-client-id>
        v
PEP Function App
Protected by Entra ID App Service Authentication
Restricted to specific MI client app + specific MI identity + tenant
        |
        | PEP validates appid / tid / aud and fixed tool contract
        | allow == true
        v
Azure Monitor Logs Connector
Uses managed identity
        |
        | RBAC: Log Analytics Data Reader
        v
Log Analytics Workspace
```
