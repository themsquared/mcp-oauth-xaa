# mcp-oauth-xaa

MCP Enterprise-Managed Authorization (Cross App Access, ID-JAG) running on your
laptop: a toy enterprise IdP, a toy MCP authorization server, and an MCP server
behind [agentgateway](https://agentgateway.dev) v1.5.0. One `docker compose`
stack, every HTTP exchange captured.

## The problem

When an MCP client connects to an MCP server, the core
[MCP authorization spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
has the user run an OAuth consent flow per server. In a company, that means
every employee authorizes every server one by one, and IT has no single place
to grant or revoke access.

[Enterprise-Managed Authorization](https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization)
(stable MCP extension) moves that decision to the corporate IdP. The client
signs the user in once, asks the IdP for an **ID-JAG** (Identity Assertion JWT
Authorization Grant,
[draft-ietf-oauth-identity-assertion-authz-grant-04](https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-assertion-authz-grant/)),
and trades that at the MCP server's authorization server for an access token.
The IdP applies group policy at the exchange step. Okta and others market the
same flow as Cross App Access (XAA).

This repo shows that exchange on the wire, including the requests that get
refused.

## What's running

| Service | Role (draft Section 2.1) | What it does |
|---|---|---|
| `idp` (`:8001`) | IdP Authorization Server | Signs users in (ID token), answers RFC 8693 token exchange with an ID-JAG after a group policy check |
| `as` (`:8002`) | Resource Authorization Server | Accepts the ID-JAG as an RFC 7523 JWT bearer assertion, issues an access token with `aud` = the MCP server |
| `notes-mcp` (`:8003`) | Resource Server (the MCP server) | Two tools, `list_notes` and `add_note`. No auth code at all |
| `gateway` (`:3000`, `:3030`) | agentgateway v1.5.0 | `:3000` is the MCP server's OAuth front door. `:3030` runs the whole exchange on the client's behalf (`backendAuth.crossAppAccess`) |
| `client` | MCP Client | Walks the flow and writes transcripts to `captures/` |

Policy in the IdP (`services/idp.py`):

| User | Group | ID-JAG scopes for the Notes AS |
|---|---|---|
| alice | engineering | `notes.read notes.write` |
| bob | contractors | `notes.read` |
| carol | sales | none. The IdP refuses the exchange |

## Quickstart

Needs Docker with Compose v2. The first build pulls `python:3.12-slim` and
`cr.agentgateway.dev/agentgateway:v1.5.0` and pip-installs PyJWT.

```bash
git clone https://github.com/themsquared/mcp-oauth-xaa.git
cd mcp-oauth-xaa
./scripts/run-all.sh
```

That starts the stack, runs five scenarios, and writes:

```
captures/alice.md               full flow, read + write
captures/bob.md                 read only, add_note refused by the gateway
captures/carol.md               IdP refuses to issue an ID-JAG
captures/alice-attacks.md       replay, token confusion, untrusted audience
captures/alice-gateway-xaa.md   agentgateway runs both exchanges itself
captures/idp.log                every request the IdP received (including the gateway's)
captures/notes-as.log           every request the authorization server received
captures/notes-mcp.log          whether an Authorization header reached the MCP server
```

Run one scenario by hand:

```bash
docker compose run --rm --no-deps client alice
docker compose run --rm --no-deps client bob
docker compose run --rm --no-deps client alice --gateway-xaa
```

Poke at it from the host. Host ports are shifted so they don't collide with
anything already on 3000 or 8001:

```bash
curl -s http://localhost:43000/.well-known/oauth-protected-resource/mcp | jq .
curl -s -i -X POST http://localhost:43000/mcp | head -4
curl -s http://localhost:48002/.well-known/oauth-authorization-server | jq .authorization_grant_profiles_supported
```

Tear down:

```bash
docker compose down
```

## The flow the client runs

1. `POST /mcp` with no token. agentgateway returns `401` with
   `WWW-Authenticate: Bearer resource_metadata="..."`.
2. Discovery: Protected Resource Metadata (RFC 9728) names the authorization
   server. Its RFC 8414 metadata lists
   `urn:ietf:params:oauth:grant-profile:id-jag` in
   `authorization_grant_profiles_supported` (EMA Section 6).
3. Sign in at the IdP and get an ID token (`aud` = the client).
4. Token exchange at the IdP: `requested_token_type=...:id-jag`,
   `audience` = the authorization server's issuer, `resource` = the MCP server.
   The IdP checks group policy and signs an ID-JAG (`typ: oauth-id-jag+jwt`).
5. JWT bearer grant at the authorization server with the ID-JAG as the
   `assertion`. It checks `typ`, signature, `aud`, `client_id` continuity and
   `jti` replay, then issues an access token with `aud` = the MCP server.
6. MCP calls with that access token. agentgateway validates it and filters
   tools by `scope`. The MCP server never sees the token.

## agentgateway config

`config/agentgateway.yaml`. Every field is in
[`schema/config.md` at v1.5.0](https://github.com/agentgateway/agentgateway/blob/v1.5.0/schema/config.md):

- `mcpAuthentication` (issuer, audiences, jwks, resourceMetadata, mode) on `:3000`
- `mcpAuthorization.rules[].allow` CEL on `jwt.scope` per tool
- `jwtAuth` + `backendAuth.crossAppAccess` on `:3030`, the policy added in
  [v1.4.0](https://github.com/agentgateway/agentgateway/releases/tag/v1.4.0)
  and documented under
  [Cross App Access](https://agentgateway.dev/docs/standalone/latest/documentation/configuration/security/backend-authn/token-exchange/cross-app-access/)

## Demo simplifications

These are choices made to keep the demo small. None of them is what the spec says.

- **Sign-in uses the password grant**, not a browser authorization code flow.
  OAuth 2.1 removes the password grant. The EMA spec expects OIDC or SAML SSO.
- **Plain HTTP and compose service names** (`http://idp:8001`). Real issuers
  are HTTPS.
- **Client secrets in source**, sent with `client_secret_basic`. The EMA spec
  also allows Client ID Metadata Documents and `private_key_jwt` at the
  authorization server.
- **Keys are generated at process start.** Restart the IdP or AS without
  restarting the gateway and every token fails with `InvalidSignature`, because
  agentgateway loads the JWKS at startup. `run-all.sh` uses `--force-recreate`.
- **The MCP server is hand-written** and returns JSON, not SSE. agentgateway
  talks to it on MCP protocol version `2025-11-25`. The authorization pieces
  exercised here (PRM, audience-bound tokens, 401 challenge) are the same in
  the `2026-07-28` authorization spec; the stateless transport changes in
  `2026-07-28` are not part of this demo.
- **Denial is an `invalid_grant`** from the IdP. The draft does not fix an
  error code for a policy refusal.
- **No DPoP, no refresh tokens, no SAML.** The draft discusses all three.
  agentgateway's docs list DPoP, `.well-known` discovery and SAML/refresh
  subject tokens as not yet supported in `crossAppAccess`.

## References

- [MCP authorization, 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [Enterprise-Managed Authorization extension](https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization) ([source](https://github.com/modelcontextprotocol/ext-auth/blob/main/specification/stable/enterprise-managed-authorization.mdx))
- [draft-ietf-oauth-identity-assertion-authz-grant-04](https://www.ietf.org/archive/id/draft-ietf-oauth-identity-assertion-authz-grant-04.html)
- [agentgateway `traffic-cross-app-access` examples](https://github.com/agentgateway/agentgateway/tree/v1.5.0/examples/traffic-cross-app-access)

## License

Apache-2.0

Topics: `mcp` `agentgateway` `oauth` `ai-agents` `identity` `enterprise-sso` `id-jag` `cross-app-access`
