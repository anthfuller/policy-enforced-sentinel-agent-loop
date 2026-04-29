## Summary

Briefly describe what changed in this PR.

## Change type

- [ ] Documentation
- [ ] Diagram
- [ ] Workflow sample
- [ ] PEP function code
- [ ] Policy/sample payload
- [ ] Tooling or validation
- [ ] Other

## Public safety checklist

- [ ] No real subscription IDs
- [ ] No real tenant IDs
- [ ] No real client IDs / application IDs
- [ ] No real object IDs
- [ ] No real managed identity names
- [ ] No real resource group names
- [ ] No real workspace names
- [ ] No real private endpoint names
- [ ] No real private DNS zone records
- [ ] No real private FQDNs
- [ ] No callback URLs or webhook URLs
- [ ] No Authorization headers
- [ ] No secrets, keys, tokens, certificates, or connection strings
- [ ] No Sentinel incident, alert, or customer data
- [ ] No run-history screenshots with identifiers
- [ ] No internal project names or customer names
- [ ] Sanitization scanner passed

## Architecture guardrails

- [ ] Agent does not generate KQL
- [ ] Agent does not select workspace, queryId, subscription, resource group, or endpoint
- [ ] Child workflow calls PEP before any Sentinel/Azure Monitor action
- [ ] Sentinel/Azure Monitor action remains only in the allow branch
- [ ] Denied, malformed, failed, or unauthorized paths fail closed
- [ ] Managed identity/RBAC is used; no embedded credentials
- [ ] Private networking assumptions are documented with placeholders only

## Validation

- [ ] README/docs reviewed
- [ ] Diagrams reviewed for sanitized labels
- [ ] Sample payloads use placeholders only
- [ ] Workflow JSON samples use placeholders only
- [ ] `tools/sanitize_check.py` was run before merge
