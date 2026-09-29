"""Minimal Streamable HTTP MCP server with two tools, list_notes and add_note.

It has no auth code at all on purpose: it only listens on the compose network,
and agentgateway in front of it is the OAuth resource server. It logs whether
an Authorization header reached it, so you can see what the gateway forwards.

JSON responses only (no SSE), which the Streamable HTTP transport allows.
"""

import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import log

NOTES = ["Q4 planning doc is in the shared drive", "On-call rotation starts Monday"]

TOOLS = [
    {
        "name": "list_notes",
        "description": "List all team notes.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_note",
        "description": "Add a team note.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]


def handle(msg):
    method = msg.get("method")
    if method == "initialize":
        return {
            "protocolVersion": msg["params"].get("protocolVersion", "2025-11-25"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "notes", "version": "0.1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments") or {}
        if name == "list_notes":
            text = "\n".join(f"- {n}" for n in NOTES)
        elif name == "add_note":
            NOTES.append(args["text"])
            text = f"added note #{len(NOTES)}"
        else:
            raise KeyError(name)
        return {"content": [{"type": "text", "text": text}], "isError": False}
    raise NotImplementedError(method)


class MCP(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/healthz":
            return self._reply(200, {"ok": True})
        # No server-initiated stream in this toy.
        self.send_response(405)
        self.end_headers()

    def do_DELETE(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        auth = self.headers.get("Authorization")
        log("notes-mcp", f"{body.get('method')} | Authorization header received: {'yes' if auth else 'no'}")
        if "id" not in body:  # notification
            self.send_response(202)
            self.end_headers()
            return
        try:
            resp = {"jsonrpc": "2.0", "id": body["id"], "result": handle(body)}
        except (KeyError, NotImplementedError) as e:
            resp = {"jsonrpc": "2.0", "id": body["id"], "error": {"code": -32601, "message": f"not found: {e}"}}
        headers = {}
        if body.get("method") == "initialize":
            headers["Mcp-Session-Id"] = uuid.uuid4().hex
        self._reply(200, resp, headers)

    def _reply(self, status, obj, headers=None):
        payload = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    log("notes-mcp", "listening on :8003")
    ThreadingHTTPServer(("0.0.0.0", 8003), MCP).serve_forever()
