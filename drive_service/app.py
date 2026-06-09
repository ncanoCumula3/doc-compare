"""
drive_service/app.py
====================
Public entrypoint. Receives Google Drive file ids AS REQUEST PARAMS, downloads
each via the reused payroll service account, flattens to text, hands them to
compare-core, and returns the ONE JSON result.

    GET/POST /compare-drive?file_ids=ID1,ID2,ID3
    GET/POST /compare-drive?file_id=ID1&file_id=ID2&file_id=ID3
    POST     /compare-drive    {"file_ids": ["ID1","ID2","ID3"]}
          -> generic comparison JSON (passed through from compare-core)

    GET /health -> {"ok": true, "drive": bool, "compare": "<url>"}

Pure stdlib + google + openpyxl + pdfplumber.
"""

import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import drive
import extract

PORT = int(os.environ.get("PORT", "8002"))
COMPARE_URL = os.environ.get("COMPARE_SERVICE_URL", "http://127.0.0.1:8001")
TIMEOUT = int(os.environ.get("COMPARE_TIMEOUT", "200"))


def _parse_ids(path, body):
    """Pull file ids from query params (file_ids=a,b,c or repeated file_id=) or JSON body."""
    ids = []
    q = urllib.parse.urlparse(path).query
    params = urllib.parse.parse_qs(q)
    for v in params.get("file_ids", []):
        ids += [x.strip() for x in v.split(",") if x.strip()]
    ids += [x.strip() for x in params.get("file_id", []) if x.strip()]
    if not ids and isinstance(body, dict):
        ids += [str(x).strip() for x in (body.get("file_ids") or []) if str(x).strip()]
    return ids


def _run(file_ids):
    documents = []
    for fid in file_ids:
        local = drive.download(fid)
        if not local:
            raise RuntimeError(f"could not download Drive file '{fid}' "
                               "(check the id and that it's shared with the service account)")
        documents.append({"name": drive.get_name(fid), "text": extract.to_text(local)})

    payload = json.dumps({"documents": documents}).encode()
    req = urllib.request.Request(
        f"{COMPARE_URL}/compare", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


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

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}
        except Exception:
            return {}

    def _handle(self, body):
        if not self.path.startswith("/compare-drive"):
            return self._send(404, {"error": "not found"})
        ids = _parse_ids(self.path, body)
        if len(ids) < 2:
            return self._send(400, {"error": "provide at least 2 file ids via "
                                    "?file_ids=a,b,c or JSON {\"file_ids\":[...]}"})
        try:
            self._send(200, _run(ids))
        except Exception as e:
            self._send(502, {"error": f"{e.__class__.__name__}: {e}"})

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True, "drive": drive.configured(),
                                    "compare": COMPARE_URL})
        self._handle({})

    def do_POST(self):
        self._handle(self._read_body())


if __name__ == "__main__":
    print(f"drive-intake on :{PORT} -> compare {COMPARE_URL} (drive configured={drive.configured()})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
