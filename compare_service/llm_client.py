"""
compare_service/llm_client.py
=============================
One client, two backends, switched by env var:

    LLM_BACKEND=ollama  ->  POST {LLM_SERVICE_URL}/analyze   (local Qwen3, default)
    LLM_BACKEND=groq    ->  Groq OpenAI-compatible endpoint  (reuses GROQ_API_KEY)

Mirrors the OpenAI-compatible call shape already used in the payroll app
(services/ai_mapper.py). Pure stdlib.
"""

import json
import os
import ssl
import urllib.request

# Verified TLS context. Prefer certifi's CA bundle if installed (fixes macOS, where
# the stdlib has no system bundle); fall back to the OS default (Render's Linux has it).
try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL = ssl.create_default_context()

BACKEND = os.environ.get("LLM_BACKEND", "ollama").lower()
TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "180"))

# ollama backend (local LLM access layer)
LLM_SERVICE_URL = os.environ.get("LLM_SERVICE_URL", "http://127.0.0.1:8000")

# groq backend (hosted open models — same key as the payroll app).
# Default to llama-4-scout: it's the one Groq model whose free-tier TPM limit is
# high enough to handle real (multi-KB) documents. qwen/qwen3-32b also works but
# its free-tier limit is 6000 TPM — fine only for small docs or a paid tier.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_MAX_TOKENS = int(os.environ.get("GROQ_MAX_TOKENS", "3000"))


def _call_ollama(system, prompt):
    payload = json.dumps({"system": system, "prompt": prompt, "json": True}).encode()
    req = urllib.request.Request(
        f"{LLM_SERVICE_URL}/analyze", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read()).get("text", "")


def _call_groq(system, prompt):
    if not GROQ_API_KEY:
        raise RuntimeError("LLM_BACKEND=groq but GROQ_API_KEY is not set")
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_completion_tokens": GROQ_MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        f"{GROQ_BASE}/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {GROQ_API_KEY}",
                 # Groq's edge blocks the default "Python-urllib/x" UA with 403.
                 "User-Agent": "doc-compare/1.0"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def analyze_json(system, prompt):
    """Run the prompt through the configured backend and parse the JSON reply."""
    raw = _call_groq(system, prompt) if BACKEND == "groq" else _call_ollama(system, prompt)
    return _parse_json(raw)


def _parse_json(text):
    """Be forgiving: strip code fences, then grab the outermost JSON object."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    try:
        return json.loads(t)
    except Exception:
        start, end = t.find("{"), t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(t[start:end + 1])
        raise


def backend_info():
    return {"backend": BACKEND,
            "target": GROQ_MODEL if BACKEND == "groq" else LLM_SERVICE_URL}
