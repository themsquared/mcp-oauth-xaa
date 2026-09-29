# Enterprise-Managed Authorization transcript: alice, agentgateway runs the exchange

The client holds only an ID token. agentgateway :3030 performs both exchanges.

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
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q",
  "access_token": "7a988ded3b5e4f049d84360cde8f1167",
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
  "iat": 1790700726,
  "auth_time": 1790700726,
  "exp": 1790701326,
  "amr": [
    "pwd"
  ]
}
```

### MCP initialize with the access token

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q
MCP-Protocol-Version: 2025-11-25
Host: gateway:3030
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "acme-agent", "version": "0.1.0"}}, "id": 1}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImZiY2JjMzI3MmYyZTQxNzFhOTdhNjkxNzg1MmY2NGY5In1dfQ

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{"tools":{}},"serverInfo":{"name":"notes","version":"0.1.0"}}}


```

### MCP notifications/initialized

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImZiY2JjMzI3MmYyZTQxNzFhOTdhNjkxNzg1MmY2NGY5In1dfQ
Host: gateway:3030
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImZiY2JjMzI3MmYyZTQxNzFhOTdhNjkxNzg1MmY2NGY5In1dfQ
Host: gateway:3030
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
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImZiY2JjMzI3MmYyZTQxNzFhOTdhNjkxNzg1MmY2NGY5In1dfQ
Host: gateway:3030
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_notes", "arguments": {}}, "id": 3}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"- Q4 planning doc is in the shared drive\n- On-call rotation starts Monday\n- note from alice\n- note from alice"}],"isError":false}}


```

### MCP tools/call add_note (needs notes.write)

```http
POST /mcp HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFjbWUtaWRwLTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vaWRwOjgwMDEiLCJzdWIiOiJVLTEwMDEiLCJhdWQiOiJhY21lLWFnZW50IiwiZW1haWwiOiJhbGljZUBhY21lLmV4YW1wbGUiLCJncm91cHMiOlsiZW5naW5lZXJpbmciXSwiaWF0IjoxNzkwNzAwNzI2LCJhdXRoX3RpbWUiOjE3OTA3MDA3MjYsImV4cCI6MTc5MDcwMTMyNiwiYW1yIjpbInB3ZCJdfQ.Y402DsggHTy6ORCWlat2ofSCd9YvfXX8MLJOB5595nSbjf-nti79Us0dGi4_bIRjnhYpYd3bSIABXDt6cnP43hOSDWGMbZEcguuv88FPPtd59Bf8Y9L6pCD3J0CTmUhl9-gbQJqOAb4gzIgAS6e7kqPv-MSdCOo7d7ED56RxhX1Ju_tMvU4qxK094NTRvp4lzrIzMpbfkWep5cRmzKHtT2cU1PtcKHzY6Egp4vK7lHAhG9YCLYlqB6yF55k4hzSM4hHgg2AXTA53U-zXTrVwD4LJH_mVLdvHgOeW6-5dZ8cNRrAfgc2Rh14KDW1-21km33n2jeyXyXUlkrsgn6-a8Q
MCP-Protocol-Version: 2025-11-25
Mcp-Session-Id: eyJ0IjoibWNwIiwicyI6W3sidCI6Im5vdGVzIiwicyI6ImZiY2JjMzI3MmYyZTQxNzFhOTdhNjkxNzg1MmY2NGY5In1dfQ
Host: gateway:3030
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_note", "arguments": {"text": "note from alice"}}, "id": 4}
```
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"added note #5"}],"isError":false}}


```
