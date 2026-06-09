"""
compare_service/app.py
======================
The reusable LLM-backed comparison engine. Domain-agnostic: hand it any
documents (as text) and it returns ONE JSON describing matches & differences.

    POST /compare   {"documents": [{"name": "...", "text": "..."}, ...]}
                 -> generic comparison JSON (see prompt.py SCHEMA_HINT)
    GET  /health -> {"ok": true, "llm": {...}}

Pure stdlib. Calling this directly with payroll docs + a census doc IS the
"analyze differences between payrolls and census" use case.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Optional CLI overrides, applied BEFORE importing llm_client (which reads these
# at import time). Args win over env vars — Render honors start-command args
# reliably, whereas inline `VAR=val cmd` env prefixes are not applied.
#   python3 app.py [backend] [llm_service_url]
if len(sys.argv) > 1 and sys.argv[1]:
    os.environ["LLM_BACKEND"] = sys.argv[1]
if len(sys.argv) > 2 and sys.argv[2]:
    os.environ["LLM_SERVICE_URL"] = sys.argv[2]

import llm_client
from prompt import SYSTEM, build_prompt

PORT = int(os.environ.get("PORT", "8001"))
# Cap per-document text so we stay inside a small model's context window.
MAX_CHARS = int(os.environ.get("MAX_DOC_CHARS", "24000"))


def compare(documents):
    docs = [{"name": d.get("name", f"doc{i+1}"),
             "text": (d.get("text") or "")[:MAX_CHARS]}
            for i, d in enumerate(documents)]
    prompt = build_prompt(docs)
    return llm_client.analyze_json(SYSTEM, prompt)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True, "llm": llm_client.backend_info()})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/compare"):
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "invalid request"})
        documents = body.get("documents")
        if not documents or not isinstance(documents, list):
            return self._send(400, {"error": "missing 'documents' list"})
        try:
            self._send(200, compare(documents))
        except Exception as e:
            # Detail to server logs only; client gets a clean, white-labelled message.
            print(f"[OakmoreLabsAI] compare error: {e.__class__.__name__}: {e}")
            self._send(502, {"error": "OakmoreLabsAI could not process the comparison"})


if __name__ == "__main__":
    print("compare-core on :%d (provider: OakmoreLabsAI)" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
