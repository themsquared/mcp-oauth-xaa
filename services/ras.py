"""Toy resource authorization server ("Notes AS") for the Notes MCP server.

Plays the Resource Authorization Server role from
draft-ietf-oauth-identity-assertion-authz-grant-04. It accepts one grant: an
ID-JAG presented as an RFC 7523 JWT bearer assertion (draft Section 4.4), and
applies the Section 4.4.1 processing rules before issuing an access token that
is audience-restricted to the MCP server (EMA Section 5.1).

Demo simplifications: one trusted IdP, hard-coded client secrets, keys
generated at startup, a replay cache that lives in process memory.
"""

import os
import threading
import uuid

import jwt

from common import (
    ID_JAG_PROFILE,
    JWT_BEARER,
    Handler,
    OAuthError,
    new_signing_key,
    now,
    serve,
)

ISSUER = os.environ.get("RAS_ISSUER", "http://as:8002")
MCP_RESOURCE = os.environ.get("MCP_RESOURCE", "http://gateway:3000/mcp")
KEY, JWKS = new_signing_key("notes-as-1")

# Clients registered at THIS authorization server. Separate from the IdP's.
CLIENTS = {"acme-agent-notes": "acme-agent-notes-ras-secret"}

# IdPs whose ID-JAGs this server honors, and where to find their keys.
TRUSTED_IDPS = {"http://idp:8001": jwt.PyJWKClient("http://idp:8001/jwks.json")}

# Local policy: the scopes this resource actually defines.
SUPPORTED_SCOPES = {"notes.read", "notes.write"}

_seen_jti = set()
_seen_lock = threading.Lock()


def metadata(_h):
    return {
        "issuer": ISSUER,
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks.json",
        "grant_types_supported": [JWT_BEARER],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"],
        "scopes_supported": sorted(SUPPORTED_SCOPES),
        # draft Section 7.2 and EMA Section 6
        "authorization_grant_profiles_supported": [ID_JAG_PROFILE],
    }


def token(h, form):
    cid, secret = h.client_credentials(form)
    if not cid or CLIENTS.get(cid) != secret:
        raise OAuthError("invalid_client", "client authentication failed", 401)
    if form.get("grant_type") != JWT_BEARER:
        raise OAuthError("unsupported_grant_type", "only jwt-bearer is accepted")

    assertion = form.get("assertion", "")
    try:
        header = jwt.get_unverified_header(assertion)
        unverified = jwt.decode(assertion, options={"verify_signature": False})
    except jwt.PyJWTError as e:
        raise OAuthError("invalid_grant", f"malformed assertion: {e}")

    # Section 4.4.1: typed JWT
    if header.get("typ") != "oauth-id-jag+jwt":
        raise OAuthError("invalid_grant", f"typ must be oauth-id-jag+jwt, got {header.get('typ')}")

    # Issuer must be an IdP we have a trust relationship with.
    jwks = TRUSTED_IDPS.get(unverified.get("iss"))
    if jwks is None:
        raise OAuthError("invalid_grant", f"untrusted issuer {unverified.get('iss')}")

    try:
        claims = jwt.decode(
            assertion,
            jwks.get_signing_key_from_jwt(assertion).key,
            algorithms=["RS256"],
            options={"verify_aud": False, "require": ["iss", "sub", "aud", "client_id", "jti", "exp", "iat"]},
        )
    except jwt.PyJWTError as e:
        raise OAuthError("invalid_grant", f"assertion rejected: {e}")

    # Section 4.4.1: aud is this server's issuer, as a string or a
    # one-element array. Anything else is audience injection.
    aud = claims["aud"]
    if isinstance(aud, list):
        aud = aud[0] if len(aud) == 1 else None
    if aud != ISSUER:
        raise OAuthError("invalid_grant", f"aud {claims['aud']!r} is not {ISSUER}")

    # Section 4.4.1: client continuity.
    if claims["client_id"] != cid:
        raise OAuthError("invalid_grant", f"ID-JAG client_id {claims['client_id']} != authenticated client {cid}")

    # RFC 7523 Section 3 allows single use; this server enforces it.
    with _seen_lock:
        if claims["jti"] in _seen_jti:
            raise OAuthError("invalid_grant", f"jti {claims['jti']} already used")
        _seen_jti.add(claims["jti"])

    resource = claims.get("resource", MCP_RESOURCE)
    if resource != MCP_RESOURCE:
        raise OAuthError("invalid_target", f"this server does not issue tokens for {resource}")

    granted = sorted(set(claims.get("scope", "").split()) & SUPPORTED_SCOPES)
    if not granted:
        raise OAuthError("invalid_scope", "no grantable scopes in the ID-JAG")

    t = now()
    access_token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": claims["sub"],
            "aud": resource,  # EMA Section 5.1: audience-restricted to the MCP server
            "client_id": cid,
            "scope": " ".join(granted),
            "email": claims.get("email"),
            "idp": claims["iss"],
            "jti": uuid.uuid4().hex,
            "iat": t,
            "exp": t + 300,
        },
        KEY,
        algorithm="RS256",
        headers={"typ": "at+jwt", "kid": "notes-as-1"},
    )
    # draft Section 4.4.2. No refresh token (Section 4.4.3).
    return {
        "token_type": "Bearer",
        "access_token": access_token,
        "expires_in": 300,
        "scope": " ".join(granted),
    }


class RAS(Handler):
    server_name = "notes-as"
    routes_get = {
        "/.well-known/oauth-authorization-server": metadata,
        "/jwks.json": lambda _h: JWKS,
        "/healthz": lambda _h: {"ok": True},
    }
    routes_post = {"/token": token}


if __name__ == "__main__":
    serve(RAS, 8002)
