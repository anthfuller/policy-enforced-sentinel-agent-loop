# Private Networking Design

## Private-by-design layers

Document the networking story as a separate layer:

1. Logic App Standard private inbound
2. Logic App Standard outbound VNet integration
3. PEP Function App private inbound
4. PEP Function App outbound networking, if required
5. Log Analytics / Azure Monitor private access
6. Private DNS resolution
7. Subnet separation
8. Validation tests

## Logic App Standard private inbound

Confirm:

- Private endpoint exists
- Private endpoint status is approved
- Private IP is assigned
- Private endpoint subnet is documented
- Private DNS zone group is attached
- Public inbound access is disabled or restricted according to policy

## Logic App Standard outbound VNet integration

Confirm:

- VNet integration is configured
- Integration subnet is dedicated for outbound integration
- NSG / UDR configuration is reviewed
- Private DNS works from the workflow runtime path

## PEP Function App private endpoint

Confirm:

- Private endpoint exists
- Private endpoint status is approved
- Private IP is assigned
- Private endpoint subnet is documented
- Private DNS zone group is attached
- Public network access is disabled or restricted
- Entra ID / App Service Authentication is enabled

The Function HTTP auth level can be anonymous only when Entra/App Service Authentication is required at the platform layer. The hardened model also restricts calls to the expected client application, specific managed identity, issuer tenant, and token audience, while the PEP validates EasyAuth claims in code.

## Azure Monitor / Sentinel private access

For private Azure Monitor / Log Analytics access, document whether Azure Monitor Private Link Scope is used.

Placeholder values:

```text
AMPLS name: <client-ampls-name>
Private endpoint name: <client-ampls-private-endpoint-name>
Workspace: <sentinel-log-analytics-workspace-name>
Workspace resource group: <workspace-resource-group>
Query access mode: <PrivateOnly-or-approved-setting>
Ingestion access mode: <PrivateOnly-or-approved-setting>
```

Known gotcha:

```text
The Azure Monitor Logs action must use the resource group that contains the Log Analytics workspace.
Do not assume it is the Logic App resource group.
```

## Private DNS zones

Document private DNS zones and VNet links.

Common zones:

```text
privatelink.azurewebsites.net
privatelink.monitor.azure.com
privatelink.oms.opinsights.azure.com
privatelink.ods.opinsights.azure.com
privatelink.blob.core.windows.net
privatelink.file.core.windows.net
privatelink.queue.core.windows.net
privatelink.table.core.windows.net
```

## Subnet layout

Example placeholder layout:

| Subnet | Purpose |
|---|---|
| snet-logicapp-integration | Logic App outbound VNet integration |
| snet-function-integration | PEP Function outbound VNet integration, if required |
| snet-private-endpoints | Private endpoints, or split per service |
| snet-ampls-private-endpoint | Azure Monitor Private Link Scope private endpoint |
| snet-management-jumpbox | Optional private validation host |

Do not mix integration subnets and private endpoint subnets without a clear design reason.

## Validation tests

From a private test host in the VNet:

```bash
nslookup <logic-app-hostname>.azurewebsites.net
nslookup <pep-function-hostname>.azurewebsites.net
```

Expected:

```text
Resolves to private IP
Does not resolve to public IP for the secured path
```

From outside the VNet:

```text
Direct calls to private Logic App and PEP endpoints should fail or be blocked according to policy.
```
