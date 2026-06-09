"""
llm_service/llm_api.py
======================
Thin Python access layer over a locally-installed Ollama model (Qwen3 4B).

"Install the LLM, then a python that gives access." Ollama serves the model on
:11434; this wrapper exposes one clean endpoint so callers never touch Ollama's
API shape directly.

    POST /analyze   {"system": "...", "prompt": "...", "json": true}
                 -> {"text": "<model output>"}
    GET  /health -> {"ok": true, "model": "qwen3:4b"}

Pure stdlib. No dependencies.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("LLM_MODEL", "qwen3:4b")
PORT = int(os.environ.get("PORT", "8000"))
TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "180"))


def _ollama_generate(system, prompt, want_json):
    """Call Ollama /api/generate (non-streaming) and return the text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system or "",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    if want_json:
        payload["format"] = "json"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        out = json.loads(resp.read())
        return out.get("response", "")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quieter logs
        pass

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True, "model": MODEL, "backend": OLLAMA_URL})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/analyze"):
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})
        prompt = body.get("prompt") or ""
        if not prompt:
            return self._send(400, {"error": "missing 'prompt'"})
        try:
            text = _ollama_generate(body.get("system", ""), prompt, bool(body.get("json")))
            self._send(200, {"text": text})
        except Exception as e:
            self._send(502, {"error": f"llm call failed: {e.__class__.__name__}: {e}"})


if __name__ == "__main__":
    print(f"llm_api on :{PORT} -> Ollama {OLLAMA_URL} model {MODEL}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
