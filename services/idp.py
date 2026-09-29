"""Toy enterprise IdP ("Acme IdP").

Plays the IdP Authorization Server role from
draft-ietf-oauth-identity-assertion-authz-grant-04 Section 2.1:

  * issues OIDC ID tokens to the MCP client at sign-in (Section 4.2), and
  * answers RFC 8693 token exchange requests for an ID-JAG (Section 4.3),
    applying an admin-defined policy table before it signs anything.

Demo simplifications (each one is called out in the README):
  * Sign-in uses the password grant instead of a browser authorization code
    flow, so the demo runs headless. OAuth 2.1 removes the password grant.
  * Users, clients, and policy are Python dicts.
  * Keys are generated at startup and never persisted.
"""

import os
import uuid

import jwt

from common import (
    ID_JAG,
    ID_TOKEN,
    TOKEN_EXCHANGE,
    Handler,
    OAuthError,
    new_signing_key,
    now,
    serve,
)

ISSUER = os.environ.get("IDP_ISSUER", "http://idp:8001")
KEY, JWKS = new_signing_key("acme-idp-1")

# The MCP client, registered with the enterprise IdP for SSO (EMA Section 7.1).
CLIENTS = {"acme-agent": "acme-agent-idp-secret"}

USERS = {
    "alice": {"password": "alice", "sub": "U-1001", "email": "alice@acme.example", "groups": ["engineering"]},
    "bob": {"password": "bob", "sub": "U-1002", "email": "bob@acme.example", "groups": ["contractors"]},
    "carol": {"password": "carol", "sub": "U-1003", "email": "carol@acme.example", "groups": ["sales"]},
}

# Resource authorization servers this IdP has a trust relationship with.
# `client_ids` maps the requesting client at the IdP to its client_id at that
# RAS, which is what goes in the ID-JAG `client_id` claim (draft Section 5).
TRUSTED_RAS = {
    "http://as:8002": {
        "client_ids": {"acme-agent": "acme-agent-notes"},
        "resources": ["http://gateway:3000/mcp"],
    }
}

# The admin console. Which groups may reach which RAS, with which scopes.
POLICY = {
    "http://as:8002": {
        "engineering": ["notes.read", "notes.write"],
        "contractors": ["notes.read"],
    }
}


def metadata(_h):
    return {
        "issuer": ISSUER,
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks.json",
        "grant_types_supported": ["password", TOKEN_EXCHANGE],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        # draft Section 7.1
        "identity_chaining_requested_token_types_supported": [ID_JAG],
    }


def authenticate_client(h, form):
    cid, secret = h.client_credentials(form)
    if not cid or CLIENTS.get(cid) != secret:
        raise OAuthError("invalid_client", "client authentication failed", 401)
    return cid


def password_grant(cid, form):
    user = USERS.get(form.get("username"))
    if not user or user["password"] != form.get("password"):
        raise OAuthError("invalid_grant", "bad username or password")
    t = now()
    id_token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": user["sub"],
            "aud": cid,
            "email": user["email"],
            "groups": user["groups"],
            "iat": t,
            "auth_time": t,
            "exp": t + 600,
            "amr": ["pwd"],
        },
        KEY,
        algorithm="RS256",
        headers={"kid": "acme-idp-1"},
    )
    return {
        "id_token": id_token,
        "access_token": uuid.uuid4().hex,
        "token_type": "Bearer",
        "scope": "openid",
        "expires_in": 600,
    }


def token_exchange(cid, form):
    # draft Section 4.3: required parameters
    if form.get("requested_token_type") != ID_JAG:
        raise OAuthError("invalid_request", "requested_token_type must be id-jag")
    if form.get("subject_token_type") != ID_TOKEN:
        raise OAuthError("invalid_request", "this IdP only accepts ID tokens as subject_token")
    audience = form.get("audience")
    ras = TRUSTED_RAS.get(audience)
    if ras is None:
        raise OAuthError("invalid_target", f"no trust relationship with {audience}")

    # draft Section 4.3.3: validate the ID token, and its audience MUST be the
    # client that authenticated this request.
    try:
        claims = jwt.decode(
            form.get("subject_token", ""),
            KEY.public_key(),
            algorithms=["RS256"],
            audience=cid,
            issuer=ISSUER,
        )
    except jwt.PyJWTError as e:
        raise OAuthError("invalid_grant", f"subject_token rejected: {e}")

    resource = form.get("resource")
    if resource and resource not in ras["resources"]:
        raise OAuthError("invalid_target", f"unknown resource {resource}")

    # Policy: the union of scopes the user's groups are allowed at this RAS.
    user = next(u for u in USERS.values() if u["sub"] == claims["sub"])
    allowed = set()
    for g in user["groups"]:
        allowed |= set(POLICY.get(audience, {}).get(g, []))
    requested = set(form.get("scope", "").split()) or allowed
    granted = sorted(requested & allowed)
    if not granted:
        raise OAuthError(
            "invalid_grant",
            f"policy: groups {user['groups']} have no access to {audience}",
        )

    t = now()
    idjag_claims = {
        "jti": uuid.uuid4().hex,
        "iss": ISSUER,
        "sub": claims["sub"],
        "email": claims["email"],
        "aud": audience,
        "client_id": ras["client_ids"][cid],
        "scope": " ".join(granted),
        "iat": t,
        "exp": t + 300,
        "auth_time": claims["auth_time"],
        "amr": claims["amr"],
    }
    if resource:
        idjag_claims["resource"] = resource
    id_jag = jwt.encode(
        idjag_claims,
        KEY,
        algorithm="RS256",
        headers={"typ": "oauth-id-jag+jwt", "kid": "acme-idp-1"},
    )
    # draft Section 4.3.4
    return {
        "issued_token_type": ID_JAG,
        "access_token": id_jag,
        "token_type": "N_A",
        "scope": " ".join(granted),
        "expires_in": 300,
    }


def token(h, form):
    cid = authenticate_client(h, form)
    grant = form.get("grant_type")
    if grant == "password":
        return password_grant(cid, form)
    if grant == TOKEN_EXCHANGE:
        return token_exchange(cid, form)
    raise OAuthError("unsupported_grant_type", f"{grant} is not supported")


class IdP(Handler):
    server_name = "idp"
    routes_get = {
        "/.well-known/oauth-authorization-server": metadata,
        "/jwks.json": lambda _h: JWKS,
        "/healthz": lambda _h: {"ok": True},
    }
    routes_post = {"/token": token}


if __name__ == "__main__":
    serve(IdP, 8001)
