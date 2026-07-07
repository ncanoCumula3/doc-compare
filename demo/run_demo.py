#!/usr/bin/env python3
import json, os, urllib.request, time
HERE=os.path.dirname(os.path.abspath(__file__)); URL="http://localhost:8001/compare"
def doc(fn): return {"name": fn, "text": open(os.path.join(HERE,fn)).read()}
CASES=[
 ("Benefits proposal vs HR census","red",["Eve","1005","Bob","tier","Family"],
   ["1_benefits_proposal.csv","1_hr_census.csv"]),
 ("Rate sheet — plan-year version diff","yellow",["435","965","Gold","Silver"],
   ["2_rates_2025.csv","2_rates_2026.csv"]),
 ("Three branch payrolls — odd one out","red",["Houston","-400","negative","2600","taxes"],
   ["3_payroll_austin.csv","3_payroll_dallas.csv","3_payroll_houston.csv"]),
 ("Contract MSA — Rev A vs Rev B","red",["250,000","250000","liability","Net 60","60"],
   ["4_msa_v1.txt","4_msa_v2.txt"]),
 ("Quarterly P&L — Q1 vs Q2","yellow",["Revenue","COGS","Net Income","52000","92000"],
   ["5_pnl_q1.csv","5_pnl_q2.csv"]),
 ("Clean roster — reordered rows/cols","green",["match"],
   ["6_roster_a.csv","6_roster_b.csv"]),
]
def post(docs):
    data=json.dumps({"documents":docs}).encode()
    req=urllib.request.Request(URL,data=data,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=180) as r: return json.loads(r.read())
passes=0
for i,(title,exp,kws,files) in enumerate(CASES,1):
    t0=time.time()
    try: res=post([doc(f) for f in files])
    except Exception as e: print(f"\n[{i}] {title}\n   ERROR: {e}"); continue
    comp=res.get("comparison",{}); status=comp.get("overall_status","?")
    blob=json.dumps(res).lower()
    finding_hit=any(str(k).lower() in blob for k in kws)
    status_ok=(status==exp) or (exp in ("red","yellow") and status in ("red","yellow"))
    ok = status_ok and finding_hit
    passes+= 1 if ok else 0
    print(f"\n[{i}] {title}   ({time.time()-t0:.0f}s)")
    print(f"    types: {[d.get('detected_type') for d in res.get('documents',[])]}")
    print(f"    status: {status}  (expected ~{exp})   finding_caught: {finding_hit}   -> {'PASS' if ok else 'CHECK'}")
    print(f"    summary: {comp.get('summary','')[:150]}")
    for d in comp.get("differences",[])[:3]:
        print(f"      - [{d.get('severity')}] {d.get('field')}: {d.get('values')}  {str(d.get('note',''))[:80]}")
print(f"\n===== {passes}/{len(CASES)} cases caught the expected finding + severity =====")
