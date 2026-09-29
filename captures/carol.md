# Enterprise-Managed Authorization transcript: carol, client-side exchange

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

### Step 3. carol signs in to the MCP client through the IdP (demo: password grant)

```http
POST /token HTTP/1.1
Authorization: Basic YWNtZS1hZ2VudDphY21lLWFnZW50LWlkcC1zZWNyZXQ=
Host: idp:8001
Content-Type: application/x-www-form-urlencoded

grant_type=password
&username=carol
&password=carol
&scope=openid
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDMiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJjYXJvbEBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsic2FsZXMiXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.CPbzXjQb52sAK0zLAM3mkZ0ZYUv-Z53fECcqfYB_DrLA8zWAvLDWSI37kTcLkKn5pgSEFznFLDIIOh5baIZyorhRtqET6ceXhHNPJfrDH4RucWW0Fg7nzL7QGylZc-vsdTIyKGcCCt_Q4nndvA8jxcq-aTSo9fRxLWMVWDBdizWD0wTCcEhIZILQZnwpGAlKJ97_ZeMKgvbZp3Gt8nwgK8XDIIlINPRbaQctlxvLUcGAfqVMaNECTanMK7mjpcNxpuHnO4tRWMtT69bOUAfNh7LR6JRNXXemIIJ4cK4IWUOB2CdhBKxQl35Ex4CXAXHmDmmm6ZAjGnOaLbd7rcTcZA",
  "access_token": "9d42107861834cdfa8a204028b8f06db",
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
  "sub": "U-1003",
  "aud": "acme-agent",
  "email": "carol@acme.example",
  "groups": [
    "sales"
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
&subject_token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDMiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJjYXJvbEBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsic2FsZXMiXSwiaWF0IjoxNzkwNzAwNzI1LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjUsImV4cCI6MTc5MDcwMTMyNSwiYW1yIjpbInB3ZCJdfQ.CPbzXjQb52sAK0zLAM3mkZ0ZYUv-Z53fECcqfYB_DrLA8zWAvLDWSI37kTcLkKn5pgSEFznFLDIIOh5baIZyorhRtqET6ceXhHNPJfrDH4RucWW0Fg7nzL7QGylZc-vsdTIyKGcCCt_Q4nndvA8jxcq-aTSo9fRxLWMVWDBdizWD0wTCcEhIZILQZnwpGAlKJ97_ZeMKgvbZp3Gt8nwgK8XDIIlINPRbaQctlxvLUcGAfqVMaNECTanMK7mjpcNxpuHnO4tRWMtT69bOUAfNh7LR6JRNXXemIIJ4cK4IWUOB2CdhBKxQl35Ex4CXAXHmDmmm6ZAjGnOaLbd7rcTcZA
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token
```
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_grant",
  "error_description": "policy: groups ['sales'] have no access to http://as:8002"
}
```

The IdP refused to issue an ID-JAG for carol. No token ever reaches the MCP server.
