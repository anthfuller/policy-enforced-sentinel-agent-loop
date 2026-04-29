# Public Repo Sanitization Checklist

## Public release checklist

Before publishing or merging changes, verify that the repository does not contain:

- Real subscription IDs
- Real tenant IDs
- Real client IDs
- Real application IDs
- Real object IDs
- Real managed identity names
- Real resource group names
- Real workspace names
- Real Function App names
- Real Logic App names
- Real private endpoint names
- Real private FQDNs
- Real callback URLs
- Real run IDs
- Real Sentinel incident numbers
- Real Sentinel query results
- Customer/client names
- Screenshots with URLs or resource identifiers
- Function keys
- API keys
- Client secrets
- Shared secrets
- Log Analytics shared keys
- Connection strings
- Tokens

## Safe placeholders

Use placeholders like:

```text
<logic-app-standard-name>
<parent-agent-workflow-name>
<child-workflow-name>
<pep-function-app-name>
<pep-app-registration-client-id>
<logic-app-pep-call-uami>
<logic-app-system-assigned-managed-identity>
<sentinel-log-analytics-workspace-name>
<workspace-resource-group>
<client-vnet-name>
<private-endpoint-subnet>
```

## Run the local scanner

```bash
python tools/sanitize_check.py .
```

This scanner provides a basic repository hygiene check for common identifiers, secrets, and environment-specific values. 
It is not a replacement for dedicated secrets scanning, code review, or manual validation.

Use it as an additional safety check before publishing or merging changes.
