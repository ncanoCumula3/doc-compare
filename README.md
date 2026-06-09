# doc-compare

LLM-driven, **domain-agnostic** document comparison. Same idea as the
payroll-validator, generalized: a local LLM *understands the format and content*
of arbitrary files, then compares them and returns one JSON. Works for payrolls,
census, contracts, financial data — no per-domain parsers.

## Three services (one repo)

```
[ drive-intake ]  3 gdrive file ids (as request params)
      |  download via reused payroll service-account key
      |  flatten each file -> text
      v
[ compare-core ]  generic LLM "understand + compare" -> ONE json
      |  http
      v
[ llm ]  Ollama + Qwen3 4B  (LLM_BACKEND=groq to use Groq instead)
```

| Service | Folder | Stack | Endpoint |
|---|---|---|---|
| llm | `llm_service/` | Docker: Ollama + Qwen3 4B + `llm_api.py` | `POST /analyze` |
| compare-core | `compare_service/` | Python stdlib | `POST /compare` |
| drive-intake | `drive_service/` | Python + google/openpyxl/pdfplumber | `GET/POST /compare-drive` |

`compare-core` is the reusable engine — POST it any documents as text and it
returns matches/differences. Calling it with payroll docs + a census doc *is*
the "payroll vs census" analysis.

## Result JSON (compare-core, passed through by drive-intake)

```json
{
  "documents": [
    {"name": "...", "detected_type": "payroll|census|contract|financial|other",
     "format": "csv|xlsx|pdf|text", "summary": "..."}
  ],
  "comparison": {
    "overall_status": "green|yellow|red",
    "summary": "...",
    "matches": ["..."],
    "differences": [
      {"field": "...", "values": {"<doc>": "<value>"},
       "severity": "green|yellow|red", "note": "..."}
    ]
  }
}
```

## Run locally

```bash
# 1) LLM — install Ollama (https://ollama.com), then:
ollama pull qwen3:4b
ollama serve &                       # serves :11434
python3 llm_service/llm_api.py       # access layer on :8000

# 2) compare-core (stdlib only)
python3 compare_service/app.py       # :8001

# 3) drive-intake (needs deps + Drive creds)
python3 -m venv .venv && . .venv/bin/activate
pip install -r drive_service/requirements.txt
#   drop the payroll app's service-account.json into drive_service/  (gitignored)
#   or export GOOGLE_SERVICE_ACCOUNT_JSON='<the json>'
python3 drive_service/app.py         # :8002
```

### Try it

```bash
# direct compare (no Drive)
curl -s localhost:8001/compare -H 'Content-Type: application/json' -d '{
  "documents": [
    {"name": "a.csv", "text": "name,pay\nAlice,100\nBob,200"},
    {"name": "b.csv", "text": "name,pay\nAlice,100\nBob,250"}
  ]}' | python3 -m json.tool

# 3 Drive files (ids as params)
curl -s "localhost:8002/compare-drive?file_ids=ID1,ID2,ID3" | python3 -m json.tool
```

### Use Groq instead of the local model

The same client talks to either backend — no code change:

```bash
export LLM_BACKEND=groq
export GROQ_API_KEY=...        # same key as the payroll app
export GROQ_MODEL=qwen/qwen3-32b
python3 compare_service/app.py
```

## Deploy on Render

`render.yaml` defines all three services. New → Blueprint → point at this repo.
Set the two secret env vars in the dashboard (same values as the payroll app):

- `doc-compare-core` → `GROQ_API_KEY`
- `doc-compare-drive` → `GOOGLE_SERVICE_ACCOUNT_JSON`

Internal URLs are wired automatically via `fromService`. The LLM service needs
the **Pro (4 GB)** plan + a 10 GB disk for the model weights — Render is CPU-only
(no GPU), so inference is a few seconds per call. If that's too slow, set
`LLM_BACKEND=groq` on `doc-compare-core` and you can drop the LLM service entirely.

## Notes

- Per-document text is capped (`MAX_DOC_CHARS`, default 24000) to fit a small
  model's context window.
- `extract.py` is intentionally dumb (file → text); the LLM does the understanding.
- Credentials are never committed — `service-account.json` and `.env` are gitignored;
  deploy via `GOOGLE_SERVICE_ACCOUNT_JSON` env only.
