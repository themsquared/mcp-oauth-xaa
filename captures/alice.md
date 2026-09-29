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
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI0LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTMyNCwiYW1yIjpbInB3ZCJdfQ.dBFgvnw1l_CpKmMqPP3icXRG8tJM7_h4D5RUh3P_EPLqoNLikYCmU3spF_mGwB-vh_eKRkqOX4POPsNHdIg1H88uhGEuBUP7exlEXMkQEi9yUIBvsghlUGgm-rowghhI9jQ1SxBZSkT7Q1l5jlN68o_szF3-byyu9ZGHwEi0bVJfaLNElma4q5sGjd4-oMRAexYKXXCKChfMLuSnDCi-ALvGpLMIvdZxz_WiNVI4i_xxhWCHzn_Y_dHzbyFGLbFkCFH20ezcdG1JJC2CgFuvXTnolHgxA8yWQIgXvvtz-8-mZZJxinYOX6HnAdTvE13upsKHtsO7w9xTzFzH01sMuw",
  "access_token": "dae691a4a9e94e5ba779293d092b2908",
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
&subject_token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI0LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTMyNCwiYW1yIjpbInB3ZCJdfQ.dBFgvnw1l_CpKmMqPP3icXRG8tJM7_h4D5RUh3P_EPLqoNLikYCmU3spF_mGwB-vh_eKRkqOX4POPsNHdIg1H88uhGEuBUP7exlEXMkQEi9yUIBvsghlUGgm-rowghhI9jQ1SxBZSkT7Q1l5jlN68o_szF3-byyu9ZGHwEi0bVJfaLNElma4q5sGjd4-oMRAexYKXXCKChfMLuSnDCi-ALvGpLMIvdZxz_WiNVI4i_xxhWCHzn_Y_dHzbyFGLbFkCFH20ezcdG1JJC2CgFuvXTnolHgxA8yWQIgXvvtz-8-mZZJxinYOX6HnAdTvE13upsKHtsO7w9xTzFzH01sMuw
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issued_token_type": "urn:ietf:params:oauth:token-type:id-jag",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJlNDZjNjRkODI2NTI0ZmNiYWI4MzgyZWRjNjcxNzZkMiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjQsImF1dGhfdGltZSI6MTc5MDcwMDcyNCwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.Rn0eglkK1LN--3lt8vE-GxDvvDrk9Qkx9681a6L3YE7ayeQbcmj_pEj-_8HkY_LOGbe-jiAUuM69Vas7xDpEMijgiWakhaSWopF9IjO8XSKlQiZSCDH7Slq9kpI3LVBV-4gzE5X1rRwwGmgJJU_O-hQF5X6NWnrSkTkITCZzey6glbPszyJqlWhgInDPZUEwIG2TS3u_32dwOyk3qlces77ahuYpoC5MrINvgsnYsLUtClyvIlLz9iFFR881qfMTaOT13MGal6vyLdLukAFUbTbDFf780XH8TlX-0Wl92By0u2FNFMyx9lxaSbomvsP8Rd1SmtLqOQjdVWSzgqTKfg",
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
  "jti": "e46c64d826524fcbab8382edc67176d2",
  "iss": "http://idp:8001",
  "sub": "U-1001",
  "email": "alice@acme.example",
  "aud": "http://as:8002",
  "client_id": "acme-agent-notes",
  "scope": "notes.read notes.write",
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
&assertion=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJvYXV0aC1pZC1qYWcrand0In0.eyJqdGkiOiJlNDZjNjRkODI2NTI0ZmNiYWI4MzgyZWRjNjcxNzZkMiIsImlzcyI6Imh0dHA6Ly9pZHA6ODAwMSIsInN1YiI6IlUtMTAwMSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiYXVkIjoiaHR0cDovL2FzOjgwMDIiLCJjbGllbnRfaWQiOiJhY21lLWFnZW50LW5vdGVzIiwic2NvcGUiOiJub3Rlcy5yZWFkIG5vdGVzLndyaXRlIiwiaWF0IjoxNzkwNzAwNzI0LCJleHAiOjE3OTA3MDEwMjQsImF1dGhfdGltZSI6MTc5MDcwMDcyNCwiYW1yIjpbInB3ZCJdLCJyZXNvdXJjZSI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIn0.Rn0eglkK1LN--3lt8vE-GxDvvDrk9Qkx9681a6L3YE7ayeQbcmj_pEj-_8HkY_LOGbe-jiAUuM69Vas7xDpEMijgiWakhaSWopF9IjO8XSKlQiZSCDH7Slq9kpI3LVBV-4gzE5X1rRwwGmgJJU_O-hQF5X6NWnrSkTkITCZzey6glbPszyJqlWhgInDPZUEwIG2TS3u_32dwOyk3qlces77ahuYpoC5MrINvgsnYsLUtClyvIlLz9iFFR881qfMTaOT13MGal6vyLdLukAFUbTbDFf780XH8TlX-0Wl92By0u2FNFMyx9lxaSbomvsP8Rd1SmtLqOQjdVWSzgqTKfg
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "token_type": "Bearer",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw",
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
  "jti": "b30a806c028349418c27efba0f908165",
  "iat": 1790700724,
  "exp": 1790701024
}
```

### MCP initialize with the access token

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw
MCP-Protocol-Version: 2025-11-25
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}, "id": 1}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6IjM1ZWQ3MmU5NTQ1NzRmNGE4YjA2YjJkZTExYmNjZWY2In1dfQ

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{"tools":{}},"serverInfo":{"name":"notes","version":"0.1.0"}}}


```

### MCP notifications/initialized

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6IjM1ZWQ3MmU5NTQ1NzRmNGE4YjA2YjJkZTExYmNjZWY2In1dfQ
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6IjM1ZWQ3MmU5NTQ1NzRmNGE4YjA2YjJkZTExYmNjZWY2In1dfQ
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6IjM1ZWQ3MmU5NTQ1NzRmNGE4YjA2YjJkZTExYmNjZWY2In1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_notes", "arguments": {}}, "id": 3}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"- Q4 planning doc is in the shared drive\n- On-call rotation starts Monday"}],"isError":false}}


```

### MCP tools/call add_note (needs notes.write)

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vdGVzLWFzLTEiLCJ0eXAiOiJhdCtqd3QifQ.eyJpc3MiOiJodHRwOi8vYXM6ODAwMiIsInN1YiI6IlUtMTAwMSIsImF1ZCI6Imh0dHA6Ly9nYXRld2F5OjMwMDAvbWNwIiwiY2xpZW50X2lkIjoiYWNtZS1hZ2VudC1ub3RlcyIsInNjb3BlIjoibm90ZXMucmVhZCBub3Rlcy53cml0ZSIsImVtYWlsIjoiYWxpY2VAYWNtZS5leGFtcGxlIiwiaWRwIjoiaHR0cDovL2lkcDo4MDAxIiwianRpIjoiYjMwYTgwNmMwMjgzNDk0MThjMjdlZmJhMGY5MDgxNjUiLCJpYXQiOjE3OTA3MDA3MjQsImV4cCI6MTc5MDcwMTAyNH0.Dxniczt0Xm80bEkGCnB8vHvJvcGbs4ikVWP8XsX44yBvMfbBPWdKiPpNlFyvuUZ2NZjcJpyNvc_V1TT3Yoi9M2E23Ekvr7QqWrL6mYZ-eYGngJuL9rCDFtLoGlX0aM_AdmcAAl4WO3hOWCt33P4t1XydfEediuxR-Pq2HNDFMWEUuuTU9lMwB-HbPvtRZqKKkMqen6MWckqVFYjWwP3BR6amIj9Lu0q9BcBaVkO9Kaoa9F9GIs5l0vjW6Yz_pD-TgmPdYbKv-apbCOYGoc18jVJmoruM1NJnOrSrg6qjf-a9gAiaYzFom1QDVBu5MX7PxNzcmU0QtyRUXIKozmDuDw
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6IjM1ZWQ3MmU5NTQ1NzRmNGE4YjA2YjJkZTExYmNjZWY2In1dfQ
Host: gateway:3000
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_note", "arguments": {"text": "note from alice"}}, "id": 4}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"added note #3"}],"isError":false}}


```
