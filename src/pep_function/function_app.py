import base64
import json
import logging
import uuid
from typing import Any

import azure.functions as func

# Public repo template:
# Replace placeholder values only in a private environment.
# AuthLevel.ANONYMOUS is intentional.
# Do not change this to FUNCTION unless you intentionally want Function keys.
# In this pattern, Entra ID / App Service Authentication is the authentication layer.
# This function also validates EasyAuth caller claims in code.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

POLICY_VERSION = "sentinel-health-query-policy-v1"

# Approved tool contract.
# Keep these values fixed for the governed tool. Do not accept them from the agent.
EXPECTED_AGENT_NAME = "<APPROVED_AGENT_NAME>"
EXPECTED_TOOL_NAME = "Sentinel Health Query"
EXPECTED_OPERATION = "sentinel.health.query"
EXPECTED_WORKSPACE = "<SENTINEL_LOG_ANALYTICS_WORKSPACE_NAME>"
EXPECTED_QUERY_ID = "sentinel_health_query_weekly_v1"

# Entra ID / App Service Authentication validation placeholders.
EXPECTED_TENANT_ID = "<ENTRA_TENANT_ID>"
EXPECTED_AUDIENCE = "api://<PEP_APP_REGISTRATION_CLIENT_ID_OR_APP_ID_URI>"

# Managed identity allowed to call this PEP endpoint.
# This should be the client/application ID of the approved Logic App managed identity.
ALLOWED_CALLER_APP_ID = "<LOGIC_APP_MANAGED_IDENTITY_CLIENT_ID>"

DENY_FIELDS = {
    "kql",
    "queryText",
    "workspaceId",
    "resourceId",
    "uri",
    "url",
    "endpoint",
    "apiKey",
    "functionKey",
    "clientSecret",
    "sharedKey",
    "connectionString",
    "token",
    "secret",
}

DENY_FIELDS_LOWER = {field.lower() for field in DENY_FIELDS}

ALLOWED_REQUEST_FIELDS = {
    "agentName",
    "toolName",
    "operation",
    "workspace",
    "queryId",
    "inputs",
    "logicAppRunId",
    "correlationId",
}


def _json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    logging.info(
        "PEP decision: allow=%s reason=%s decisionId=%s",
        payload.get("allow"),
        payload.get("reason"),
        payload.get("decisionId"),
    )

    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


def _decision_base(data: dict | None, reason: str) -> dict:
    data = data if isinstance(data, dict) else {}

    return {
        "allow": False,
        "decisionId": str(uuid.uuid4()),
        "policyVersion": POLICY_VERSION,
        "reason": reason,
        "toolName": data.get("toolName"),
        "operation": data.get("operation"),
        "workspace": data.get("workspace"),
        "queryId": data.get("queryId"),
    }


def _deny(data: dict | None, reason: str, status_code: int = 200) -> func.HttpResponse:
    return _json_response(_decision_base(data, reason), status_code)


def _header(req: func.HttpRequest, name: str) -> str | None:
    for key, value in req.headers.items():
        if key.lower() == name.lower():
            return value
    return None


def _decode_easy_auth_principal(req: func.HttpRequest) -> dict[str, Any] | None:
    encoded = _header(req, "x-ms-client-principal")
    if not encoded:
        return None

    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        return json.loads(decoded)
    except Exception as exc:
        logging.warning("Failed to decode x-ms-client-principal: %s", exc)
        return None


def _claim_value(principal: dict[str, Any], claim_names: set[str]) -> str | None:
    claims = principal.get("claims", [])

    for claim in claims:
        typ = str(claim.get("typ", "")).lower()
        val = claim.get("val")

        for name in claim_names:
            name_l = name.lower()
            if typ == name_l or typ.endswith("/" + name_l) or typ.endswith("/claims/" + name_l):
                return val

    return None


def _verify_entra_caller(req: func.HttpRequest) -> str | None:
    idp = _header(req, "x-ms-client-principal-idp")
    if idp and idp.lower() not in {"aad", "microsoft"}:
        return f"invalid identity provider: {idp}"

    principal = _decode_easy_auth_principal(req)
    if not principal:
        return "missing EasyAuth principal"

    caller_app_id = _claim_value(principal, {"appid", "azp", "client_id"})
    tenant_id = _claim_value(principal, {"tid", "tenantid"})
    audience = _claim_value(principal, {"aud"})

    if caller_app_id != ALLOWED_CALLER_APP_ID:
        return "caller managed identity appId mismatch"

    if tenant_id != EXPECTED_TENANT_ID:
        return "tenantId mismatch"

    if audience != EXPECTED_AUDIENCE:
        return "token audience mismatch"

    return None


def _contains_forbidden_key(obj: Any) -> str | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in DENY_FIELDS_LOWER:
                return str(key)

            nested = _contains_forbidden_key(value)
            if nested:
                return nested

    elif isinstance(obj, list):
        for item in obj:
            nested = _contains_forbidden_key(item)
            if nested:
                return nested

    return None


@app.route(route="pep_evaluate", methods=["POST"])
def pep_evaluate(req: func.HttpRequest) -> func.HttpResponse:
    auth_error = _verify_entra_caller(req)
    if auth_error:
        return _deny(None, f"unauthorized caller: {auth_error}", status_code=401)

    try:
        data = req.get_json()
    except ValueError:
        return _json_response(
            {
                "allow": False,
                "decisionId": str(uuid.uuid4()),
                "policyVersion": POLICY_VERSION,
                "reason": "malformed JSON request",
                "toolName": None,
                "operation": None,
                "workspace": None,
                "queryId": None,
            },
            200,
        )

    if not isinstance(data, dict):
        return _deny({}, "request body must be a JSON object")

    unexpected_fields = set(data.keys()) - ALLOWED_REQUEST_FIELDS
    if unexpected_fields:
        return _deny(data, f"unexpected field detected: {sorted(unexpected_fields)}")

    forbidden_key = _contains_forbidden_key(data)
    if forbidden_key:
        return _deny(data, f"forbidden field detected: {forbidden_key}")

    if data.get("agentName") != EXPECTED_AGENT_NAME:
        return _deny(data, "agentName mismatch")

    if data.get("toolName") != EXPECTED_TOOL_NAME:
        return _deny(data, "toolName mismatch")

    if data.get("operation") != EXPECTED_OPERATION:
        return _deny(data, "operation mismatch")

    if data.get("workspace") != EXPECTED_WORKSPACE:
        return _deny(data, "workspace mismatch")

    if data.get("queryId") != EXPECTED_QUERY_ID:
        return _deny(data, "queryId mismatch")

    if data.get("inputs") != {}:
        return _deny(data, "inputs must be empty")

    return _json_response(
        {
            "allow": True,
            "decisionId": str(uuid.uuid4()),
            "policyVersion": POLICY_VERSION,
            "reason": "PEP allow: fixed Sentinel health query is authorized",
            "toolName": EXPECTED_TOOL_NAME,
            "operation": EXPECTED_OPERATION,
            "workspace": EXPECTED_WORKSPACE,
            "queryId": EXPECTED_QUERY_ID,
        },
        200,
    )
