"""Shared helpers for the toy IdP and the toy resource authorization server.

Everything here is demo-grade: keys are generated in memory at startup, client
secrets are hard-coded, and there is no TLS. Do not reuse any of it for real.
"""

import base64
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
JWT_BEARER = "urn:ietf:params:oauth:grant-type:jwt-bearer"
ID_JAG = "urn:ietf:params:oauth:token-type:id-jag"
ID_TOKEN = "urn:ietf:params:oauth:token-type:id_token"
ID_JAG_PROFILE = "urn:ietf:params:oauth:grant-profile:id-jag"


def new_signing_key(kid):
    """Generate an RSA key and its public JWKS. Lives only as long as the process."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return key, {"keys": [jwk]}


class OAuthError(Exception):
    """An RFC 6749 Section 5.2 token error response."""

    def __init__(self, error, description, status=400):
        super().__init__(description)
        self.error = error
        self.description = description
        self.status = status


def log(name, text):
    print(f"[{name}] {text}", file=sys.stdout, flush=True)


class Handler(BaseHTTPRequestHandler):
    """Base handler: form parsing, client authentication, JSON replies, and a
    full request/response log on stdout so `docker compose logs` shows the wire."""

    server_name = "server"
    routes_get = {}
    routes_post = {}

    def log_message(self, fmt, *args):  # silence the default access log
        pass

    # --- helpers -----------------------------------------------------------
    def form(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode() if length else ""
        self._raw_body = raw
        return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

    def client_credentials(self, form):
        """client_secret_basic or client_secret_post. Returns (client_id, secret)."""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            decoded = base64.b64decode(auth[6:]).decode()
            cid, _, secret = decoded.partition(":")
            return cid, secret
        return form.get("client_id"), form.get("client_secret")

    def send_json(self, status, body, extra_headers=None):
        payload = json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        self._log_exchange(status, body)

    def _log_exchange(self, status, body):
        if self.path == "/healthz":
            return
        lines = [f"{self.command} {self.path}"]
        for h in ("Host", "Authorization", "Content-Type"):
            if self.headers.get(h):
                lines.append(f"{h}: {self.headers.get(h)}")
        raw = getattr(self, "_raw_body", "")
        if raw:
            lines.append("")
            lines.append(raw.replace("&", "\n&"))
        lines.append(f"--> {status}")
        lines.append(json.dumps(body, indent=2))
        log(self.server_name, "\n".join(lines) + "\n")

    # --- dispatch ----------------------------------------------------------
    def do_GET(self):
        fn = self.routes_get.get(self.path)
        if fn is None:
            return self.send_json(404, {"error": "not_found"})
        return self.send_json(200, fn(self))

    def do_POST(self):
        fn = self.routes_post.get(self.path)
        if fn is None:
            return self.send_json(404, {"error": "not_found"})
        try:
            form = self.form()
            return self.send_json(200, fn(self, form))
        except OAuthError as e:
            return self.send_json(
                e.status, {"error": e.error, "error_description": e.description}
            )


def serve(handler_cls, port):
    log(handler_cls.server_name, f"listening on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), handler_cls).serve_forever()


def now():
    return int(time.time())
