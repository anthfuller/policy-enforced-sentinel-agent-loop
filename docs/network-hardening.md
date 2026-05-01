# Network Hardening and AMPLS Design Note

## Purpose

This document explains the network-hardening scope for this demo and how the architecture can be extended for stricter production deployments using Azure Monitor Private Link Scope (AMPLS).

The demo focuses on proving **policy enforcement and governed tool execution** for an autonomous agent workflow that interacts with Microsoft Sentinel.

## Why AMPLS Is Not Required for the Core Demo

This means the agent cannot directly query Sentinel.

The agent can only request an approved tool path. The Policy Enforcement Point (PEP) must authorize the request before the Sentinel query action runs.

AMPLS strengthens the network path to Azure Monitor / Log Analytics, but it is not required to prove the core governance pattern.

## Demo Architecture

In the demo architecture:

```text
Logic App Standard
→ outbound VNET integration
→ Function App Private Endpoint
→ Azure Function PEP
→ allow / deny decision
→ Azure Monitor Logs connector
→ Log Analytics Workspace / Microsoft Sentinel
```

The Function App PEP is reached through a private endpoint.

The Log Analytics Workspace remains accessible through its standard Azure Monitor / Log Analytics endpoint for demo usability.

## Production Hardening Option: AMPLS

For stricter private-network deployments, the Log Analytics Workspace can be added to an Azure Monitor Private Link Scope (AMPLS).

A hardened deployment path would be:

```text
Logic App Standard
→ outbound VNET integration
→ Azure Monitor Logs connector
→ Azure Monitor Private Link Scope (AMPLS)
→ Private Endpoint
→ Log Analytics Workspace / Microsoft Sentinel
```

In this model, Sentinel / Log Analytics query traffic can be forced through a private network path.

## AMPLS Caveats

Enabling AMPLS can affect how analysts and tools query Log Analytics / Sentinel data.

Portal sign-in is not blocked by AMPLS. Users can still sign in to:

- Azure portal
- Microsoft Sentinel
- Microsoft Defender XDR portal

However, if Log Analytics public query access is restricted, then query experiences may require access from a private network path such as:

- Jump box
- VPN
- ExpressRoute
- VNET-connected admin workstation
- Approved SOC network path

Examples:

```text
From jump box / VPN / VNET path → expected to work
From normal public internet workstation → Log Analytics queries may fail
```

This can affect:

- Sentinel Logs
- Hunting queries
- KQL query experiences
- LAW-backed query views
- Some Sentinel-integrated investigation workflows

## Recommended Use

### Demo / POC Environment

For a demo or proof-of-concept focused on agent governance:

- Keep Log Analytics public query access enabled
- Prove the PEP allow / deny path
- Prove fixed-query enforcement
- Prove the agent cannot generate KQL or select a workspace
- Document AMPLS as an optional production-hardening control

### Production / High-Security Environment

For stricter enterprise deployments:

- Add the Log Analytics Workspace to AMPLS
- Create a private endpoint for AMPLS
- Configure required private DNS zones
- Validate query access from approved private network paths
- Consider restricting public query access only after private access is tested
- Ensure SOC analysts have a supported private access path
- Validate Sentinel portal, Logs, Hunting, and Defender XDR integrations before enforcement

## Microsoft References

- [Secure traffic between Standard logic apps and Azure virtual networks using private endpoints](https://learn.microsoft.com/en-us/azure/logic-apps/secure-single-tenant-workflow-virtual-network-private-endpoint)
- [Integrate your app with an Azure virtual network](https://learn.microsoft.com/en-us/azure/app-service/overview-vnet-integration)
- [Use Azure Private Link to connect networks to Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-security)
- [Configure private link for Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-configure)


```markdown
> **Network hardening note:** This demo uses a private endpoint for the Azure Function PEP and outbound VNET integration from Logic App Standard. The Log Analytics Workspace does not use AMPLS in the demo environment. For a stricter private-network deployment, see [Network Hardening and AMPLS Design Note](docs/network-hardening.md).
```
