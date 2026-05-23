from __future__ import annotations

import base64
import json


class AuthError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _decode_jwt_payload(token: str) -> dict[str, object]:
    """Decode JWT payload without signature verification.

    WARNING: This does NOT verify the token signature. Production deployments
    must validate the signature using the Entra External ID JWKS endpoint.
    Signature verification will be completed in M1.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed JWT: expected 3 parts")
    padding = 4 - len(parts[1]) % 4
    padded = parts[1] + "=" * (padding % 4)
    try:
        payload_bytes = base64.urlsafe_b64decode(padded)
        result: dict[str, object] = json.loads(payload_bytes)
        return result
    except Exception as exc:
        raise AuthError("Failed to decode JWT payload") from exc


def extract_client_id_from_token(token: str) -> str:
    """Extract the clientId claim from a validated Bearer JWT.

    Uses the 'azp' (authorized party / client_id) claim, which Entra External ID
    sets to the app registration client ID for client-credentials tokens.
    Falls back to 'oid' (object ID) for user tokens.
    """
    payload = _decode_jwt_payload(token)

    client_id = payload.get("azp") or payload.get("oid")
    if not client_id or not isinstance(client_id, str):
        raise AuthError("JWT is missing 'azp' and 'oid' claims")
    return client_id


def extract_bearer_token(authorization: str) -> str:
    """Parse the raw Authorization header value and return the token."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("Authorization header must use Bearer scheme")
    return token
