# Enterprise-Managed Authorization transcript: bob, client-side exchange

Every request below was sent by services/client.py and every response is verbatim.

### Step 1. Call the MCP server with no token

```http
POST /mcp HTTP/1.1
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}}
```
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer resource_metadata="http://gateway:3000/.well-known/oauth-protected-resource/mcp"

{
  "error": "unauthorized",
  "error_description": "JWT token required"
}
```

### Step 2a. Fetch Protected Resource Metadata (RFC 9728)

```http
GET /.well-known/oauth-protected-resource/mcp HTTP/1.1
Host: gateway:3000
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "resource": "http://gateway:3000/mcp",
  "authorization_servers": [
    "http://as:8002"
  ],
  "mcp_protocol_version": "2025-06-18",
  "resource_type": "mcp-server",
  "bearer_methods_supported": [
    "header"
  ],
  "scopes_supported": [
    "notes.read",
    "notes.write"
  ]
}
```

### Step 2b. Fetch the MCP authorization server's metadata (RFC 8414)

```http
GET /.well-known/oauth-authorization-server HTTP/1.1
Host: as:8002
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issuer": "http://as:8002",
  "token_endpoint": "http://as:8002/token",
  "jwks_uri": "http://as:8002/jwks.json",
  "grant_types_supported": [
    "urn:ietf:params:oauth:grant-type:jwt-bearer"
  ],
  "token_endpoint_auth_methods_supported": [
    "client_secret_basic"
  ],
  "scopes_supported": [
    "notes.read",
    "notes.write"
  ],
  "authorization_grant_profiles_supported": [
    "urn:ietf:params:oauth:grant-profile:id-jag"
  ]
}
```

### Step 2c. Fetch the enterprise IdP's metadata

```http
GET /.well-known/oauth-authorization-server HTTP/1.1
Host: idp:8001
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issuer": "http://idp:8001",
  "token_endpoint": "http://idp:8001/token",
  "jwks_uri": "http://idp:8001/jwks.json",
  "grant_types_supported": [
    "password",
    "urn:ietf:params:oauth:grant-type:token-exchange"
  ],
  "token_endpoint_auth_methods_supported": [
    "client_secret_basic",
    "client_secret_post"
  ],
  "identity_chaining_requested_token_types_supported": [
    "urn:ietf:params:oauth:token-type:id-jag"
  ]
}
```

### Step 3. bob signs in to the MCP client through the IdP (demo: password grant)

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudDphY21lLWFnZW50LWlkcC1zZWNyZXQ=
Host: idp:8001
Content-Type: application/x-www-form-urlencoded

grant_type=password
&username=bob
&password=bob
&scope=openid
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDIiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJib2JAYWNtZS5leGFtcGxlIiwiZ3JvdXBzIjpbImNvbnRyYWN0b3JzIl0sImlhdCI6MTc5MDcwMDcyNCwiYXV0aF90aW1lIjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEzMjQsImFtciI6WyJwd2QiXX0.M4fSLmT_tyxuXfJaz66sm-dedxixmXVSA8dAFVS70TfnrCycjicMd9WSNtErDdid5OplDkRYiATUAlSq6GVGuqAuppotifewXBPpOoGGQ0c2M6nljfjnfTW-y8I28fZmWqvSEsE-jRi9GjFfehKQ-xglkTO_sgLjsboI3zn2bfTfvFsWPROQpNN3eQpq6Dj6POv5EwKXBnpY1Ru5cKyXEf8f4uehq-P3EyFj0g6R7VmbVtWTSZQ6ILxdAuMJungrT6l4VVW01rnXjf6CYScGUc-OVDVcFNjdbfWeF7gHt0eHEXeNLvF_oBn3sRORrNJieEit_SgmRNVgc_UARQ0FfQ",
  "access_token": "3be8e45ac5084c8a8d8fd57815cb9e91",
  "token_type": "Bearer",
  "scope": "openid",
  "expires_in": 600
}
```

ID token (decoded):
```json
{
  "alg": "RS256",
  "kid": "acme-idp-1",
  "typ": "JWT"
}
{
  "iss": "http://idp:8001",
  "sub": "U-1002",
  "aud": "acme-agent",
  "email": "bob@acme.example",
  "groups": [
    "contractors"
  ],
  "iat": 1790700724,
  "auth_time": 1790700724,
  "exp": 1790701324,
  "amr": [
    "pwd"
  ]
}
```

### Step 4. Exchange the ID token for an ID-JAG at the IdP (RFC 8693)

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudDphY21lLWFnZW50LWlkcC1zZWNyZXQ=
Host: idp:8001
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange
&requested_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid-jag
&audience=http%3A%2F%2Fas%3A8002
&resource=http%3A%2F%2Fgateway%3A3000%2Fmcp
&scope=notes.read+notes.write
&subject_token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDIiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJib2JAYWNtZS5leGFtcGxlIiwiZ3JvdXBzIjpbImNvbnRyYWN0b3JzIl0sImlhdCI6MTc5MDcwMDcyNCwiYXV0aF90aW1lIjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEzMjQsImFtciI6WyJwd2QiXX0.M4fSLmT_tyxuXfJaz66sm-dedxixmXVSA8dAFVS70TfnrCycjicMd9WSNtErDdid5OplDkRYiATUAlSq6GVGuqAuppotifewXBPpOoGGQ0c2M6nljfjnfTW-y8I28fZmWqvSEsE-jRi9GjFfehKQ-xglkTO_sgLjsboI3zn2bfTfvFsWPROQpNN3eQpq6Dj6POv5EwKXBnpY1Ru5cKyXEf8f4uehq-P3EyFj0g6R7VmbVtWTSZQ6ILxdAuMJungrT6l4VVW01rnXjf6CYScGUc-OVDVcFNjdbfWeF7gHt0eHEXeNLvF_oBn3sRORrNJieEit_SgmRNVgc_UARQ0FfQ
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issued_token_type": "urn:ietf:params:oauth:token-type:id-jag",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJiZGQ0Y2M4NmVmNDU0NzRiYjk2ZjgyMTFmZGI5NTgxOSIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMiIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImF1ZCI6Imh0dHA6Ly9hczo4MDAyIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImlhdCI6MTc5MDcwMDcyNCwiZXhwIjoxNzkwNzAxMDI0LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjQsImFtciI6WyJwd2QiXSwicmVzb3VyY2UiOiJodHRwOi8vZ2F0ZXdheTozMDAwL21jcCJ9.g8FT-czqdhBxySv-INjrsidRF-p1LqVvoBjibzoxCC7RqRzKM-lNYmreq5AQSwg-Yv6dMB7BZogku0Hek489hHRbGNfyIrgU4dyfVsMIc14oJfHEFljuAcqnXSZZNuC82ZW4ArmaeuA_FyGtt9ra2IlGGoCB3_SDgzymrNKIQyBCphmmZ0rU6IDoYHfN9XdpKoKt8RpSgEdJ2T5O8PIrdVJVWErLhwGBcm7OHTAlFOGEoYYz2fRJazQZuismSzHQ7b6SaUGj62MoZ9W_-nF-EUli4AGrvRFg97YE-AxEAsoVnqCy_5gXvdeohQ9FhfVyBJxuxrVcFPGr45oal-8QBQ",
  "token_type": "N_A",
  "scope": "notes.read",
  "expires_in": 300
}
```

ID-JAG (decoded):
```json
{
  "alg": "RS256",
  "kid": "acme-idp-1",
  "typ": "oauth-id-jag+jwt"
}
{
  "jti": "bdd4cc86ef45474bb96f8211fdb95819",
  "iss": "http://idp:8001",
  "sub": "U-1002",
  "email": "bob@acme.example",
  "aud": "http://as:8002",
  "client_id": "acme-agent-notes",
  "scope": "notes.read",
  "iat": 1790700724,
  "exp": 1790701024,
  "auth_time": 1790700724,
  "amr": [
    "pwd"
  ],
  "resource": "http://gateway:3000/mcp"
}
```

### Step 5. Present the ID-JAG to the MCP authorization server (RFC 7523)

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudC1ub3RlczphY21lLWFnZW50LW5vdGVzLXJhcy1zZWNyZXQ=
Host: as:8002
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer
&assertion=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJiZGQ0Y2M4NmVmNDU0NzRiYjk2ZjgyMTFmZGI5NTgxOSIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMiIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImF1ZCI6Imh0dHA6Ly9hczo4MDAyIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImlhdCI6MTc5MDcwMDcyNCwiZXhwIjoxNzkwNzAxMDI0LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjQsImFtciI6WyJwd2QiXSwicmVzb3VyY2UiOiJodHRwOi8vZ2F0ZXdheTozMDAwL21jcCJ9.g8FT-czqdhBxySv-INjrsidRF-p1LqVvoBjibzoxCC7RqRzKM-lNYmreq5AQSwg-Yv6dMB7BZogku0Hek489hHRbGNfyIrgU4dyfVsMIc14oJfHEFljuAcqnXSZZNuC82ZW4ArmaeuA_FyGtt9ra2IlGGoCB3_SDgzymrNKIQyBCphmmZ0rU6IDoYHfN9XdpKoKt8RpSgEdJ2T5O8PIrdVJVWErLhwGBcm7OHTAlFOGEoYYz2fRJazQZuismSzHQ7b6SaUGj62MoZ9W_-nF-EUli4AGrvRFg97YE-AxEAsoVnqCy_5gXvdeohQ9FhfVyBJxuxrVcFPGr45oal-8QBQ
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "token_type": "Bearer",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ",
  "expires_in": 300,
  "scope": "notes.read"
}
```

MCP access token (decoded):
```json
{
  "alg": "RS256",
  "kid": "notes-as-1",
  "typ": "at+jwt"
}
{
  "iss": "http://as:8002",
  "sub": "U-1002",
  "aud": "http://gateway:3000/mcp",
  "client_id": "acme-agent-notes",
  "scope": "notes.read",
  "email": "bob@acme.example",
  "idp": "http://idp:8001",
  "jti": "36763a95dbfb44a69824bd1289910a14",
  "iat": 1790700724,
  "exp": 1790701024
}
```

### MCP initialize with the access token

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}, "id": 1}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImQ2MjRjYTg2MTY5ZjRiNmU4MDNmMzhiOThiMGZkNDhmIn1dfQ

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{"tools":{}},"serverInfo":{"name":"notes","version":"0.1.0"}}}


```

### MCP notifications/initialized

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImQ2MjRjYTg2MTY5ZjRiNmU4MDNmMzhiOThiMGZkNDhmIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "notifications/initialized"}
```
```http
HTTP/1.1 202 Accepted
```

### MCP tools/list (filtered by the token's scope)

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImQ2MjRjYTg2MTY5ZjRiNmU4MDNmMzhiOThiMGZkNDhmIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"list_notes","description":"List all team notes.","inputSchema":{"type":"object","properties":{}}}]}}


```

### MCP tools/call list_notes

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImQ2MjRjYTg2MTY5ZjRiNmU4MDNmMzhiOThiMGZkNDhmIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_notes", "arguments": {}}, "id": 3}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"- Q4 planning doc is in the shared drive\n- On-call rotation starts Monday\n- note from alice"}],"isError":false}}


```

### MCP tools/call add_note (needs notes.write)

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMiIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCIsImVtYWlsIjoiYm9iQGFjbWUuZXhhbXBsZSIsImlkcCI6Imh0dHA6Ly9pZHA6ODAwMSIsImp0aSI6IjM2NzYzYTk1ZGJmYjQ0YTY5ODI0YmQxMjg5OTEwYTE0IiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjR9.aJ1icNoUU-dFaqcAFz7Q6W0B_3dIl1qBLjGQmMJAUR7o6dnJ06A0whQzKUHOP7yd4hjp-7asZo9pwMXG-tAr8tiCASKZhzlUgoOE3xXegsgyrKsJ76J_bqw7PhFncuRINn4oO9JeZ0Q6HbRJRQCt6r0LL5XMAYWz3ZiG2DpDf1TeyANM2WhxwR2iGJMORtBOXur48w16pVptjjxITc8ZD7zrKfOzyA8DHdwKGo-7Ginfh6srUPAsCgdUe7FAL4FL2PSZWJKkKMIygFux0_j2hf6A23JgdDZmlusY4YgS-NVohpqT4p9gz5FG2VK8TwkmJ4UISr5FlHtTiCDiBf_DwQ
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImQ2MjRjYTg2MTY5ZjRiNmU4MDNmMzhiOThiMGZkNDhmIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_note", "arguments": {"text": "note from bob"}}, "id": 4}
```
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 4,
  "error": {
    "code": -32602,
    "message": "Unknown tool: add_note"
  }
}
```
