# Enterprise-Managed Authorization transcript: alice, client-side exchange

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

### Step 3. alice signs in to the MCP client through the IdP (demo: password grant)

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudDphY21lLWFnZW50LWlkcC1zZWNyZXQ=
Host: idp:8001
Content-Type: application/x-www-form-urlencoded

grant_type=password
&username=alice
&password=alice
&scope=openid
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.MQUPn61uBX2OmR8Fs3E0H3_mHXmiNN6VmhQO4bOXe5vXfQVxCRO3UIHQUYE73xX3D38tZXm9BFGUwbKeYulpC1CHVZ6tcoAjFZozxf7tkUsBElVl5urSX52jOnVIyFSFjfNmGbUKBRbge4QLY9D5d74D30wHDGVyaCMu70QezER6qDEVduCZw-u_VzCXwikkaKNlPowPRw4eTvhHw4MWBFhbAEOqBc0_B3b53r4wQSao7Zx7R2Sd7y7xDklx5I3yQk8MAfAT3R2GXWpZ27Y3uDERFzRpc_evJJ6FNTwj_laEFYX2HBkTsIghTcsNG3CwylkPCTc037ocG7PBg5O6dw",
  "access_token": "bf67083560f14358b9cbd29e7cc625c3",
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
  "sub": "U-1001",
  "aud": "acme-agent",
  "email": "alice@acme.example",
  "groups": [
    "engineering"
  ],
  "iat": 1790700725,
  "auth_time": 1790700725,
  "exp": 1790701325,
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
&subject_token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.MQUPn61uBX2OmR8Fs3E0H3_mHXmiNN6VmhQO4bOXe5vXfQVxCRO3UIHQUYE73xX3D38tZXm9BFGUwbKeYulpC1CHVZ6tcoAjFZozxf7tkUsBElVl5urSX52jOnVIyFSFjfNmGbUKBRbge4QLY9D5d74D30wHDGVyaCMu70QezER6qDEVduCZw-u_VzCXwikkaKNlPowPRw4eTvhHw4MWBFhbAEOqBc0_B3b53r4wQSao7Zx7R2Sd7y7xDklx5I3yQk8MAfAT3R2GXWpZ27Y3uDERFzRpc_evJJ6FNTwj_laEFYX2HBkTsIghTcsNG3CwylkPCTc037ocG7PBg5O6dw
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issued_token_type": "urn:ietf:params:oauth:token-type:id-jag",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJhY2Y3YTY1ZDhmZTM0NjI1ODdlYTczNWE2ODJjNDYwZiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI1LCJleHAiOjE3OTA3MDEwMjUsImF1dGhfdGltZSI6MTc5MDcwMDcyNSwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.BQGnkJ_5tqWtvyPYESsIsaljxq-fgeuD_BGLrxvKSuZiXEPJdNNYFrv_qPHpa0RnVIr-BxdPFVYZXgTSuOYM-kr2wgBfkcF27_auaRAtLNwenmut9uxKYV56GL_te7tvsgR_e0gLxGy0Xl0UQm0nvwsbrhbxkf31doUR1s-DGXmdRO9WvqjBhVBE9N2EoQirpOXNU6WQo4qFXfI0VmMmQmKMBNh9cmjt6PqpY4ZAAZeXwJMrc4vyuYM49zrjuojnirION9GxEZLaS1gOelMs92jfLuYezknp9QJOI1Tpx9Ex7BrVKj5szUvsD4CZboK_JPwvVFgNbtnjmlWL6S4r-w",
  "token_type": "N_A",
  "scope": "notes.read notes.write",
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
  "jti": "acf7a65d8fe3462587ea735a682c460f",
  "iss": "http://idp:8001",
  "sub": "U-1001",
  "email": "alice@acme.example",
  "aud": "http://as:8002",
  "client_id": "acme-agent-notes",
  "scope": "notes.read notes.write",
  "iat": 1790700725,
  "exp": 1790701025,
  "auth_time": 1790700725,
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
&assertion=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJhY2Y3YTY1ZDhmZTM0NjI1ODdlYTczNWE2ODJjNDYwZiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI1LCJleHAiOjE3OTA3MDEwMjUsImF1dGhfdGltZSI6MTc5MDcwMDcyNSwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.BQGnkJ_5tqWtvyPYESsIsaljxq-fgeuD_BGLrxvKSuZiXEPJdNNYFrv_qPHpa0RnVIr-BxdPFVYZXgTSuOYM-kr2wgBfkcF27_auaRAtLNwenmut9uxKYV56GL_te7tvsgR_e0gLxGy0Xl0UQm0nvwsbrhbxkf31doUR1s-DGXmdRO9WvqjBhVBE9N2EoQirpOXNU6WQo4qFXfI0VmMmQmKMBNh9cmjt6PqpY4ZAAZeXwJMrc4vyuYM49zrjuojnirION9GxEZLaS1gOelMs92jfLuYezknp9QJOI1Tpx9Ex7BrVKj5szUvsD4CZboK_JPwvVFgNbtnjmlWL6S4r-w
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "token_type": "Bearer",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw",
  "expires_in": 300,
  "scope": "notes.read notes.write"
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
  "sub": "U-1001",
  "aud": "http://gateway:3000/mcp",
  "client_id": "acme-agent-notes",
  "scope": "notes.read notes.write",
  "email": "alice@acme.example",
  "idp": "http://idp:8001",
  "jti": "c3a354d3449045c7bae08712abd06759",
  "iat": 1790700725,
  "exp": 1790701025
}
```

### MCP initialize with the access token

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}, "id": 1}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImY0OGM2MTFhY2M3MjRhMWU5MGY1OTIyNTQwNTBmY2MwIn1dfQ

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{"tools":{}},"serverInfo":{"name":"notes","version":"0.1.0"}}}


```

### MCP notifications/initialized

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImY0OGM2MTFhY2M3MjRhMWU5MGY1OTIyNTQwNTBmY2MwIn1dfQ
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImY0OGM2MTFhY2M3MjRhMWU5MGY1OTIyNTQwNTBmY2MwIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"list_notes","description":"List all team notes.","inputSchema":{"type":"object","properties":{}}},{"name":"add_note","description":"Add a team note.","inputSchema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}]}}


```

### MCP tools/call list_notes

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImY0OGM2MTFhY2M3MjRhMWU5MGY1OTIyNTQwNTBmY2MwIn1dfQ
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYzNhMzU0ZDM0NDkwNDVjN2JhZTA4NzEyYWJkMDY3NTkiLCJpYXQiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTAyNX0.QTf361oCw4uSmEVHHitSDfcb4AeASnWS_ZYyzH7FoKZv-BuwI8hQMOstlub2KM_q9Zd9hDLaLi1atAKO1zeokGguoMy-CdqclMrWJJSG8D_Ckh-B-tNAJiVuTOpxgGV2PZMxCcgqoVJcI-7VwbX-4wMCqQVJXx-9y_MghAjOvxQAXO5Z44hCgQWGWxb-BAca9Hes_s_s1IQwUaKzZC1-rErbr7TXselApXIDYC4pE5mIj2l14agPxyMkr50GhFeNTNf1F6w5FIpwp6HK-fMEY9mFwNqsIRVU4uQ-5lsEIFrvULXI6IV8FpoKuEQByedCINsokweDoOdI7k8uFl0cbw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImY0OGM2MTFhY2M3MjRhMWU5MGY1OTIyNTQwNTBmY2MwIn1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_note", "arguments": {"text": "note from alice"}}, "id": 4}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"added note #4"}],"isError":false}}


```

## What gets rejected


### Replay the same ID-JAG at the authorization server

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudC1ub3RlczphY21lLWFnZW50LW5vdGVzLXJhcy1zZWNyZXQ=
Host: as:8002
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer
&assertion=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJhY2Y3YTY1ZDhmZTM0NjI1ODdlYTczNWE2ODJjNDYwZiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI1LCJleHAiOjE3OTA3MDEwMjUsImF1dGhfdGltZSI6MTc5MDcwMDcyNSwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.BQGnkJ_5tqWtvyPYESsIsaljxq-fgeuD_BGLrxvKSuZiXEPJdNNYFrv_qPHpa0RnVIr-BxdPFVYZXgTSuOYM-kr2wgBfkcF27_auaRAtLNwenmut9uxKYV56GL_te7tvsgR_e0gLxGy0Xl0UQm0nvwsbrhbxkf31doUR1s-DGXmdRO9WvqjBhVBE9N2EoQirpOXNU6WQo4qFXfI0VmMmQmKMBNh9cmjt6PqpY4ZAAZeXwJMrc4vyuYM49zrjuojnirION9GxEZLaS1gOelMs92jfLuYezknp9QJOI1Tpx9Ex7BrVKj5szUvsD4CZboK_JPwvVFgNbtnjmlWL6S4r-w
```
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_grant",
  "error_description": "jti acf7a65d8fe3462587ea735a682c460f already used"
}
```

### Send the ID-JAG straight to the MCP server as a bearer token

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJhY2Y3YTY1ZDhmZTM0NjI1ODdlYTczNWE2ODJjNDYwZiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI1LCJleHAiOjE3OTA3MDEwMjUsImF1dGhfdGltZSI6MTc5MDcwMDcyNSwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.BQGnkJ_5tqWtvyPYESsIsaljxq-fgeuD_BGLrxvKSuZiXEPJdNNYFrv_qPHpa0RnVIr-BxdPFVYZXgTSuOYM-kr2wgBfkcF27_auaRAtLNwenmut9uxKYV56GL_te7tvsgR_e0gLxGy0Xl0UQm0nvwsbrhbxkf31doUR1s-DGXmdRO9WvqjBhVBE9N2EoQirpOXNU6WQo4qFXfI0VmMmQmKMBNh9cmjt6PqpY4ZAAZeXwJMrc4vyuYM49zrjuojnirION9GxEZLaS1gOelMs92jfLuYezknp9QJOI1Tpx9Ex7BrVKj5szUvsD4CZboK_JPwvVFgNbtnjmlWL6S4r-w
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 9}
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

### Send the IdP ID token straight to the MCP server

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.MQUPn61uBX2OmR8Fs3E0H3_mHXmiNN6VmhQO4bOXe5vXfQVxCRO3UIHQUYE73xX3D38tZXm9BFGUwbKeYulpC1CHVZ6tcoAjFZozxf7tkUsBElVl5urSX52jOnVIyFSFjfNmGbUKBRbge4QLY9D5d74D30wHDGVyaCMu70QezER6qDEVduCZw-u_VzCXwikkaKNlPowPRw4eTvhHw4MWBFhbAEOqBc0_B3b53r4wQSao7Zx7R2Sd7y7xDklx5I3yQk8MAfAT3R2GXWpZ27Y3uDERFzRpc_evJJ6FNTwj_laEFYX2HBkTsIghTcsNG3CwylkPCTc037ocG7PBg5O6dw
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 9}
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

### Present the ID token (not an ID-JAG) to the authorization server

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudC1ub3RlczphY21lLWFnZW50LW5vdGVzLXJhcy1zZWNyZXQ=
Host: as:8002
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer
&assertion=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.MQUPn61uBX2OmR8Fs3E0H3_mHXmiNN6VmhQO4bOXe5vXfQVxCRO3UIHQUYE73xX3D38tZXm9BFGUwbKeYulpC1CHVZ6tcoAjFZozxf7tkUsBElVl5urSX52jOnVIyFSFjfNmGbUKBRbge4QLY9D5d74D30wHDGVyaCMu70QezER6qDEVduCZw-u_VzCXwikkaKNlPowPRw4eTvhHw4MWBFhbAEOqBc0_B3b53r4wQSao7Zx7R2Sd7y7xDklx5I3yQk8MAfAT3R2GXWpZ27Y3uDERFzRpc_evJJ6FNTwj_laEFYX2HBkTsIghTcsNG3CwylkPCTc037ocG7PBg5O6dw
```
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_grant",
  "error_description": "typ must be oauth-id-jag+jwt, got JWT"
}
```

### Ask the IdP for an ID-JAG aimed at an authorization server it has no trust with

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudDphY21lLWFnZW50LWlkcC1zZWNyZXQ=
Host: idp:8001
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange
&requested_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid-jag
&audience=http%3A%2F%2Fevil-as.example
&subject_token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.MQUPn61uBX2OmR8Fs3E0H3_mHXmiNN6VmhQO4bOXe5vXfQVxCRO3UIHQUYE73xX3D38tZXm9BFGUwbKeYulpC1CHVZ6tcoAjFZozxf7tkUsBElVl5urSX52jOnVIyFSFjfNmGbUKBRbge4QLY9D5d74D30wHDGVyaCMu70QezER6qDEVduCZw-u_VzCXwikkaKNlPowPRw4eTvhHw4MWBFhbAEOqBc0_B3b53r4wQSao7Zx7R2Sd7y7xDklx5I3yQk8MAfAT3R2GXWpZ27Y3uDERFzRpc_evJJ6FNTwj_laEFYX2HBkTsIghTcsNG3CwylkPCTc037ocG7PBg5O6dw
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token
```
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_target",
  "error_description": "no trust relationship with http://evil-as.example"
}
```
