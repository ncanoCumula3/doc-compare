"""
compare_service/prompt.py
=========================
The one generic prompt that makes this domain-agnostic. The LLM is asked to
FIRST understand each document's type/format, THEN compare them — so the same
code works for payrolls, census, contracts, financial data, etc.
"""

SYSTEM = (
    "You are a meticulous data analyst. You receive several documents of unknown "
    "type (payroll, census, contract, financial statement, etc.). You identify "
    "what each document is, then compare them and report matches and differences. "
    "You respond with ONLY valid JSON — no prose, no markdown fences."
)

# The result schema, embedded in the prompt so the model fills the right shape.
SCHEMA_HINT = """Return ONLY a JSON object with exactly this shape:
{
  "documents": [
    {"name": "<doc name>", "detected_type": "payroll|census|contract|financial|other",
     "format": "csv|xlsx|pdf|text", "summary": "<one sentence>"}
  ],
  "comparison": {
    "overall_status": "green|yellow|red",
    "summary": "<one short paragraph: do these documents agree?>",
    "matches": ["<things that agree across the documents>"],
    "differences": [
      {"field": "<what differs>",
       "values": {"<doc name>": "<value in that doc>"},
       "severity": "green|yellow|red",
       "note": "<why it differs / why it matters>"}
    ]
  }
}
Severity guide: green = identical or within rounding; yellow = minor/explainable
difference; red = material mismatch worth investigating. If a document is missing
an entity or field present in others, that is a difference."""


def build_prompt(documents):
    """documents: [{"name": str, "text": str}, ...] -> a single user prompt string."""
    parts = [
        f"There are {len(documents)} documents to compare. "
        "Identify each one, then compare them.\n",
    ]
    for i, d in enumerate(documents, 1):
        parts.append(f"\n===== DOCUMENT {i}: {d.get('name', f'doc{i}')} =====\n")
        parts.append(d.get("text", ""))
    parts.append("\n\n" + SCHEMA_HINT)
    return "".join(parts)
