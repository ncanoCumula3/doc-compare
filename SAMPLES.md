# doc-compare — real samples

Live examples against real Google Drive files. The endpoint takes 2–N Drive file
ids as params and returns one JSON. Provider is white-labelled as **OakmoreLabsAI**.

```
GET https://doc-compare-drive.onrender.com/compare-drive?file_ids=ID1,ID2,ID3
```

Every response has the same shape:

```json
{
  "documents":  [ {"name","detected_type","format","summary"}, ... ],
  "comparison": {
    "overall_status": "green|yellow|red",
    "summary": "...",
    "matches": [ "..." ],
    "differences": [ {"field","values":{"<doc>":"<value>"},"severity","note"} ]
  }
}
```

---

## Sample A — 3 files (detect versions + odd-one-out)

Two revisions of one client + an unrelated client.

**Request**
```
GET /compare-drive?file_ids=1U4y_jLVaHJGVDMccpQSXhOasPIRAuoa2,14NHEPaWYOOS5imNLnwGTxkDGOQbJ8eW5,1QLAqUQnluqwAQgCl-U81jHPp7qCmkKnm
```
(Joe's Pizza v1, Joe's Pizza v2, MD Plumbing Co)

**Response**
```json
{
  "documents": [
    {"name": "Joe's Pizza.xlsx", "detected_type": "payroll", "format": "xlsx",
     "summary": "Payroll document for Joe's Pizza, listing employee information and benefits."},
    {"name": "Joe's Pizza.xlsx", "detected_type": "payroll", "format": "xlsx",
     "summary": "Another payroll document for Joe's Pizza, possibly a duplicate or updated version."},
    {"name": "MD Plumbing Co.xlsx", "detected_type": "payroll", "format": "xlsx",
     "summary": "Payroll document for MD Plumbing Co, listing employee information and benefits."}
  ],
  "comparison": {
    "overall_status": "yellow",
    "summary": "The documents are payroll records for different companies, with similar structures but distinct data.",
    "matches": ["similar structure and fields", "presence of employee names, salaries, and benefits"],
    "differences": [
      {"field": "Company Name", "values": {"Joe's Pizza.xlsx": "Joe's Pizza", "MD Plumbing Co.xlsx": "MD Plumbing Co"}, "severity": "green", "note": "Different companies"},
      {"field": "Work State", "values": {"Joe's Pizza.xlsx": "IL", "MD Plumbing Co.xlsx": "NC"}, "severity": "green", "note": "Different states"},
      {"field": "Salary Ranges", "values": {"Joe's Pizza.xlsx": "$1,998 - $149,084", "MD Plumbing Co.xlsx": "$17,813 - $110,000"}, "severity": "yellow", "note": "Different salary ranges"}
    ]
  }
}
```

---

## Sample B — version diff (what changed between two revisions)

Same client, two file versions. Different comparison *type* — surfaces the rows that changed.

**Request**
```
GET /compare-drive?file_ids=1U4y_jLVaHJGVDMccpQSXhOasPIRAuoa2,14NHEPaWYOOS5imNLnwGTxkDGOQbJ8eW5
```
(Joe's Pizza v1 vs v2)

**Response**
```json
{
  "documents": [
    {"name": "Joe's Pizza.xlsx", "detected_type": "payroll", "format": "xlsx", "summary": "Payroll document for Joe's Pizza: salaries, taxes, benefits."},
    {"name": "Joe's Pizza.xlsx", "detected_type": "payroll", "format": "xlsx", "summary": "Another payroll document for Joe's Pizza, similar details."}
  ],
  "comparison": {
    "overall_status": "yellow",
    "summary": "Two similar payroll documents for Joe's Pizza, with discrepancies in employee data and calculations.",
    "matches": ["Same columns and structure.", "Same employees with similar job info.", "State and federal tax calculations consistent."],
    "differences": [
      {"field": "Annual Salary", "values": {"Joe's Pizza.xlsx": "104936.00"}, "severity": "red", "note": "Significant difference in annual salary for Michelle Albers."},
      {"field": "Salary With Buffer And Premium", "values": {"Joe's Pizza.xlsx": "90860"}, "severity": "red", "note": "Significant difference for Michelle Albers."},
      {"field": "Employee Monthly Allotment", "values": {"Joe's Pizza.xlsx": "1076.83"}, "severity": "yellow", "note": "Difference in employee monthly allotment."}
    ]
  }
}
```

---

## Sample C — proposal vs census (the core payroll use case)

**Request**
```
GET /compare-drive?file_ids=17AkdSALUiTkrA_3wsQ5nDMzY4DQC3rrh,1F4qnrXMw7vQAg0lV0aAjOIpbMUuo4k58
```
(GD Correctional proposal.xlsx + Master Census.csv)

**Response**
```json
{
  "documents": [
    {"name": "GD Correctional ... .xlsx", "detected_type": "payroll", "format": "xlsx", "summary": "Payroll report with employee details and salary information."},
    {"name": "GD Correctional ... Master Census - 6.3.26.csv", "detected_type": "census", "format": "csv", "summary": "Census report with employee demographic and compensation information."}
  ],
  "comparison": {
    "overall_status": "yellow",
    "summary": "The documents generally agree on employee details and compensation, with some discrepancies in formatting and specific values.",
    "matches": ["Employee names and IDs match.", "Gross annual salaries match for most employees.", "State and pay frequency consistent."],
    "differences": [
      {"field": "Federal W-4 Marital Status", "values": {"proposal.xlsx": "Not provided", "census.csv": "S, H"}, "severity": "yellow", "note": "Marital status absent in the proposal; census shows S (single) / H (head of household)."},
      {"field": "Additional Federal and State Withholding", "values": {"proposal.xlsx": "Not provided", "census.csv": "Some values provided"}, "severity": "yellow", "note": "Census provides extra withholding info."},
      {"field": "Employee Monthly Contribution for Group Health", "values": {"proposal.xlsx": "Included in calculations", "census.csv": "Not explicitly mentioned"}, "severity": "yellow", "note": "Group-health contribution in the proposal but not the census."}
    ]
  }
}
```

---

## Sample D — 3-version chain (one client, three revisions)

**Request**
```
GET /compare-drive?file_ids=1jkyNUigkycmCJLIC-AWWOF8kV_BQhNxt,1rrLbnyIyHBxdymf1-VZkxWEFOaWQ7T4o,1fZrz9FnOokpsevI8pTc8pe3c7w5On6UJ
```
(Roth Farms additions v1, v2, reviewed `ara`)

**Response** (key part)
```json
{
  "comparison": {
    "overall_status": "yellow",
    "summary": "The documents largely agree but have some formatting and minor data differences.",
    "matches": ["Employee names and IDs match", "Annual salaries match", "State/location consistent"],
    "differences": [
      {"field": "Column names and order", "values": {"v1/v2": "First Name, Last Name, Annual Salary...", "ara": "Client Name, Employee Last Name, Employee First Name..."}, "severity": "yellow", "note": "Reworked layout, same underlying info"},
      {"field": "Group Health (Employee Monthly Contribution)", "values": {"v1/v2": "Not present in this format", "ara": "771.05"}, "severity": "yellow", "note": "Field added in the reviewed version"}
    ]
  }
}
```

---

## Sample E — cross-industry odd-one-out (real data-quality catch)

**Request**
```
GET /compare-drive?file_ids=1clIH2fiouZ_rI6jHEZn0BN6X3tIv8fXC,1OtOTufzqOA9rt1m5cnXJr9jbsH7iWgRt,1U4y_jLVaHJGVDMccpQSXhOasPIRAuoa2
```
(Transco Lines [trucking] + AVS Audio Engineering + Joe's Pizza)

**Response** (key part)
```json
{
  "comparison": {
    "overall_status": "yellow",
    "summary": "Similar payroll reports, with differences in employee info, salary and tax.",
    "differences": [
      {"field": "Annual Salary", "values": {"Transco Lines.xlsx": "all 0.00", "AVS Audio Engineering.xlsx": "varies (65000, 37440)", "Joe's Pizza.xlsx": "varies (2018, 3471)"}, "severity": "red", "note": "Annual salary is 0.00 for ALL employees in Transco Lines — likely a data error."},
      {"field": "Work State", "values": {"Transco Lines.xlsx": "varies (OK, MS, AR)", "AVS Audio Engineering.xlsx": "all AL", "Joe's Pizza.xlsx": "all IL"}, "severity": "red", "note": "Multi-state vs single-state operations."}
    ]
  }
}
```
> Note: caught that **Transco Lines has $0.00 salary for every employee** — a real data-quality flag, surfaced with no rule written for it.

---

## Sample F — proposal vs census, material RED finding

**Request**
```
GET /compare-drive?file_ids=1rXPINNlWkkDKYywCjqd5lnJCMKltJbeH,1k3L6SBO0JCd8ArEVCbULoAgf3CoVshRZ
```
(Marco Plastics proposal.xlsx + Master Census.xlsx)

**Response** (key part)
```json
{
  "comparison": {
    "overall_status": "yellow",
    "differences": [
      {"field": "Gross Annual Wages", "values": {"proposal": "52000.00, 50000.08, 37440.00, 61347.00", "census": "52000, 50000.08, 37440, 61347"}, "severity": "green", "note": "Identical, minor rounding."},
      {"field": "Employee Monthly Contribution (Health)", "values": {"proposal": "89, 89, 89, 89", "census": "29.62, 22.97, 29.62, 279.65"}, "severity": "red", "note": "Significant discrepancy in health contributions — proposal uses a flat 89, census has actuals."},
      {"field": "401-k/IRA Monthly Amount", "values": {"proposal": "230.5, 219.83, 208.01, 322.3", "census": "Not directly comparable"}, "severity": "yellow", "note": "401k present in proposal, absent in census."}
    ]
  }
}
```

---

## Big files & version pairs

The largest files in the Drive (up to 80 KB), compared successfully. On Groq's free
tier these need to be spaced ~1/min (per-minute token budget) and each document is
read up to the first ~15 KB; for unlimited size/volume use the local OakmoreLabsAI
engine or a paid tier.

**Sample G — Family Matters, 70 KB version pair** (`Home Service` vs `Home Services`)
→ `green`, **no differences** — the two revisions are identical.

**Sample H — Transco Lines v1 vs v2** → `red`:
```json
{"field": "Annual Salary", "values": {"v1": "detailed", "v2": "0.00 for all employees"},
 "severity": "red", "note": "v2 is an empty/template version — all values zero."}
```

**Sample I — American R&C original vs `Updated ara`** → `yellow`: state taxes, health
contributions, and 401-k/Medicare deductions differ between the two revisions.

**Sample J — Township of Parsippany (80 KB) proposal vs census** → `yellow`: label
mismatch (`Annual Salary` vs `Gross Annual TAXABLE Wages`) and differing detail levels.

**Sample K — Nissan Guam proposal vs census** → `red`:
```json
{"field": "Employee Count", "values": {"Nissan Guam.xlsx": "around 40", "Master Census": "around 80"},
 "severity": "red", "note": "Significant difference in number of employees listed."}
```

---

## Document types available in this Drive

The connected Drive currently holds only Attentive proposal-tool spreadsheets
(`.xlsx` proposals + `.csv`/`.xlsx` censuses) — no PDFs/contracts/financials. Even
so, the same generic engine supports several comparison *types* on them:

| Type | Example | What it surfaces |
|---|---|---|
| Proposal vs census | Sample C | field/value mismatches between projection and source data |
| Version diff | Sample B | what changed between two revisions of one file |
| Multi-doc / odd-one-out | Sample A | which document doesn't belong; cross-entity differences |

Because the LLM reads format + content generically, dropping a contract, invoice,
or financial statement into the same endpoint works with no code changes — those
just aren't present in this Drive yet.
