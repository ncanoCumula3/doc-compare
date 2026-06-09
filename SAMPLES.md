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
