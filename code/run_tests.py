"""Runs the final workflow on every test case, saves the outputs and writes the test table.
Usage: python run_tests.py"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import resumeiq
from evaluate import check

ROOT = Path(__file__).resolve().parent.parent
CASES = json.loads((ROOT / "test-data/inputs/test_cases.json").read_text())
OUT = ROOT / "test-data/outputs/final"


def short_actual(res: dict) -> str:
    if res.get("valid") is False:
        return f"Rejected: {res.get('problem')}"
    met = [m["requirement"] for m in res.get("matches", []) if m.get("status") == "match"]
    part = [m["requirement"] for m in res.get("matches", []) if m.get("status") == "partial"]
    miss = [m["requirement"] for m in res.get("matches", []) if m.get("status") == "missing"]
    s = f"Score {res.get('score')}. Match: {', '.join(met) or '-'}. Partial: {', '.join(part) or '-'}. Missing: {', '.join(miss) or '-'}."
    if res.get("warnings"):
        s += " Warning: " + " ".join(res["warnings"])
    return s


def one(case):
    res = resumeiq.run_final(case["resume"], case["jd"])
    chk = check(case, res)
    (OUT / f"{case['id']}.json").write_text(json.dumps({"input": case, "output": res, "check": chk}, indent=1, ensure_ascii=False))
    return case, res, chk


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(one, CASES))
    rows = ["| Test | Input (short) | Type | Expected output | Actual output (short) | Pass/Fail |", "|---|---|---|---|---|---|"]
    for case, res, chk in results:
        rows.append(f"| {case['id']} | {case['title']} | {case['type']} | {case['expected']} | {short_actual(res)} | {'Pass' if chk['passed'] else 'Fail'} |")
    passed = sum(c["passed"] for _, _, c in results)
    table = "\n".join(rows)
    (OUT / "test_table.md").write_text(f"Run on {datetime.now():%Y-%m-%d %H:%M} UTC. Passed {passed}/{len(results)}.\n\n{table}\n")
    print(table)
    print(f"\nPassed {passed}/{len(results)}")
    for case, res, chk in results:
        print(case["id"], chk)
