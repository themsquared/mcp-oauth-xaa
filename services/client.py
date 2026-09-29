"""MCP client that walks Enterprise-Managed Authorization end to end and prints
every HTTP exchange it makes, plus decoded JWTs.

  python3 client.py alice            # client-side exchange, the spec's flow
  python3 client.py bob              # same, IdP policy grants read only
  python3 client.py carol            # IdP policy denies the exchange
  python3 client.py alice --attacks  # also try the token-confusion cases
  python3 client.py alice --gateway-xaa   # let agentgateway run the exchange

A transcript lands in /captures/<user>[-mode].md.
"""

import base64
import http.client
import json
import sys
from urllib.parse import urlencode, urlparse

IDP = "http://idp:8001"  # the enterprise IdP this client does SSO with
MCP_URL = "http://gateway:3000/mcp"
GATEWAY_XAA_URL = "http://gateway:3030/mcp"
IDP_CLIENT = ("acme-agent", "acme-agent-idp-secret")
RAS_CLIENT = ("acme-agent-notes", "acme-agent-notes-ras-secret")
PROTOCOL_VERSION = "2025-11-25"

OUT = []


def out(s=""):
    print(s)
    OUT.append(s)


def b64url_json(part):
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def show_jwt(label, token):
    h, p, _ = token.split(".")
    out(f"\n{label} (decoded):\n```json")
    out(json.dumps(b64url_json(h), indent=2))
    out(json.dumps(b64url_json(p), indent=2))
    out("```")


def basic(cid, secret):
    return "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()


def http_call(method, url, headers=None, form=None, note="", json_body=None):
    """One HTTP exchange, printed exactly as sent and received."""
    u = urlparse(url)
    headers = dict(headers or {})
    headers.setdefault("Host", u.netloc)
    body = None
    if form is not None:
        body = urlencode(form)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif json_body is not None:
        body = json.dumps(json_body)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json, text/event-stream"

    out(f"\n### {note}\n" if note else "")
    out("```http")
    out(f"{method} {u.path or '/'} HTTP/1.1")
    for k, v in headers.items():
        out(f"{k}: {v}")
    if body:
        out("")
        out(body.replace("&", "\n&") if headers.get("Content-Type", "").startswith("application/x-www") else body)
    out("```")

    conn = http.client.HTTPConnection(u.hostname, u.port, timeout=15)
    conn.request(method, u.path or "/", body=body, headers=headers)
    r = conn.getresponse()
    data = r.read().decode()
    out("```http")
    out(f"HTTP/1.1 {r.status} {r.reason}")
    for k in ("Content-Type", "WWW-Authenticate", "Mcp-Session-Id"):
        if r.getheader(k):
            out(f"{k}: {r.getheader(k)}")
    if data:
        out("")
        try:
            out(json.dumps(json.loads(data), indent=2))
        except json.JSONDecodeError:
            out(data)
    out("```")
    try:
        parsed = json.loads(data) if data else None
    except json.JSONDecodeError:
        parsed = data
    return r.status, {k.lower(): v for k, v in r.getheaders()}, parsed


def rpc(url, token, method, params=None, id_=None, session=None, note=""):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if id_ is not None:
        msg["id"] = id_
    headers = {"Authorization": f"Bearer {token}", "MCP-Protocol-Version": PROTOCOL_VERSION}
    if session:
        headers["Mcp-Session-Id"] = session
    return http_call("POST", url, headers, note=note or f"MCP {method}", json_body=msg)


def mcp_session(url, token, user):
    init = {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "acme-agent", "version": "0.1.0"},
    }
    status, hdrs, _ = rpc(url, token, "initialize", init, 1, note="MCP initialize with the access token")
    if status != 200:
        return
    session = hdrs.get("mcp-session-id")
    rpc(url, token, "notifications/initialized", session=session, note="MCP notifications/initialized")
    rpc(url, token, "tools/list", {}, 2, session, note="MCP tools/list (filtered by the token's scope)")
    rpc(url, token, "tools/call", {"name": "list_notes", "arguments": {}}, 3, session, note="MCP tools/call list_notes")
    rpc(
        url,
        token,
        "tools/call",
        {"name": "add_note", "arguments": {"text": f"note from {user}"}},
        4,
        session,
        note="MCP tools/call add_note (needs notes.write)",
    )


def sso_login(user):
    """Demo stand-in for OIDC SSO (EMA Section 3): password grant, no browser."""
    _, _, tok = http_call(
        "POST",
        f"{IDP}/token",
        {"Authorization": basic(*IDP_CLIENT)},
        {"grant_type": "password", "username": user, "password": user, "scope": "openid"},
        f"Step 3. {user} signs in to the MCP client through the IdP (demo: password grant)",
    )
    show_jwt("ID token", tok["id_token"])
    return tok["id_token"]


def client_side_flow(user, attacks):
    out(f"# Enterprise-Managed Authorization transcript: {user}, client-side exchange\n")
    out("Every request below was sent by services/client.py and every response is verbatim.")

    # Step 1. Unauthenticated MCP request -> 401 with resource_metadata
    status, hdrs, _ = http_call(
        "POST",
        MCP_URL,
        {"MCP-Protocol-Version": PROTOCOL_VERSION},
        note="Step 1. Call the MCP server with no token",
        json_body={"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}},
    )
    www = hdrs.get("www-authenticate", "")
    prm_url = www.split('resource_metadata="')[1].split('"')[0]

    # Step 2. Discovery: Protected Resource Metadata, then AS metadata
    _, _, prm = http_call("GET", prm_url, note="Step 2a. Fetch Protected Resource Metadata (RFC 9728)")
    ras = prm["authorization_servers"][0]
    _, _, ras_meta = http_call(
        "GET", f"{ras}/.well-known/oauth-authorization-server", note="Step 2b. Fetch the MCP authorization server's metadata (RFC 8414)"
    )
    assert "urn:ietf:params:oauth:grant-profile:id-jag" in ras_meta["authorization_grant_profiles_supported"]
    _, _, idp_meta = http_call(
        "GET", f"{IDP}/.well-known/oauth-authorization-server", note="Step 2c. Fetch the enterprise IdP's metadata"
    )

    id_token = sso_login(user)

    # Step 4. Token exchange at the IdP -> ID-JAG
    status, _, tx = http_call(
        "POST",
        idp_meta["token_endpoint"],
        {"Authorization": basic(*IDP_CLIENT)},
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requested_token_type": "urn:ietf:params:oauth:token-type:id-jag",
            "audience": ras_meta["issuer"],
            "resource": prm["resource"],
            "scope": "notes.read notes.write",
            "subject_token": id_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
        },
        "Step 4. Exchange the ID token for an ID-JAG at the IdP (RFC 8693)",
    )
    if status != 200:
        out(f"\nThe IdP refused to issue an ID-JAG for {user}. No token ever reaches the MCP server.")
        return
    id_jag = tx["access_token"]
    show_jwt("ID-JAG", id_jag)

    # Step 5. JWT bearer grant at the MCP authorization server -> access token
    _, _, at = http_call(
        "POST",
        ras_meta["token_endpoint"],
        {"Authorization": basic(*RAS_CLIENT)},
        {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": id_jag},
        "Step 5. Present the ID-JAG to the MCP authorization server (RFC 7523)",
    )
    access_token = at["access_token"]
    show_jwt("MCP access token", access_token)

    # Step 6. MCP with the access token
    mcp_session(MCP_URL, access_token, user)

    if attacks:
        out("\n## What gets rejected\n")
        http_call(
            "POST",
            ras_meta["token_endpoint"],
            {"Authorization": basic(*RAS_CLIENT)},
            {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": id_jag},
            "Replay the same ID-JAG at the authorization server",
        )
        rpc(MCP_URL, id_jag, "tools/list", {}, 9, note="Send the ID-JAG straight to the MCP server as a bearer token")
        rpc(MCP_URL, id_token, "tools/list", {}, 9, note="Send the IdP ID token straight to the MCP server")
        http_call(
            "POST",
            ras_meta["token_endpoint"],
            {"Authorization": basic(*RAS_CLIENT)},
            {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": id_token},
            "Present the ID token (not an ID-JAG) to the authorization server",
        )
        http_call(
            "POST",
            idp_meta["token_endpoint"],
            {"Authorization": basic(*IDP_CLIENT)},
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "requested_token_type": "urn:ietf:params:oauth:token-type:id-jag",
                "audience": "http://evil-as.example",
                "subject_token": id_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
            },
            "Ask the IdP for an ID-JAG aimed at an authorization server it has no trust with",
        )


def gateway_xaa_flow(user):
    out(f"# Enterprise-Managed Authorization transcript: {user}, agentgateway runs the exchange\n")
    out("The client holds only an ID token. agentgateway :3030 performs both exchanges.")
    id_token = sso_login(user)
    mcp_session(GATEWAY_XAA_URL, id_token, user)


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "alice"
    gw = "--gateway-xaa" in sys.argv
    if gw:
        gateway_xaa_flow(user)
    else:
        client_side_flow(user, "--attacks" in sys.argv)
    name = f"{user}{'-gateway-xaa' if gw else ''}{'-attacks' if '--attacks' in sys.argv else ''}"
    with open(f"/captures/{name}.md", "w") as f:
        f.write("\n".join(OUT) + "\n")
