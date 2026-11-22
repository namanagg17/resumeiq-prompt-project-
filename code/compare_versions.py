"""Runs prompt versions v1-v4 on the same inputs and records the numbers used in the
prompt iteration log. Usage: python compare_versions.py v1 v2 v3 v4 v5"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import resumeiq
from evaluate import check

ROOT = Path(__file__).resolve().parent.parent
CASES = {c["id"]: c for c in json.loads((ROOT / "test-data/inputs/test_cases.json").read_text())}
REPEAT_CASES = ["T01", "T04", "T05"]   # run 3 times each: score consistency
SINGLE_CASES = ["T11", "T13"]          # prompt injection, invalid input
REPEATS = 3


def run_version(version: str) -> dict:
    jobs = [(cid, i) for cid in REPEAT_CASES for i in range(REPEATS)] + [(cid, 0) for cid in SINGLE_CASES]
    runner = resumeiq.RUNNERS[version]

    def one(job):
        cid, i = job
        case = CASES[cid]
        res = runner(case["resume"], case["jd"])
        return {"case": cid, "run": i + 1, "result": res, "check": check(case, res)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(one, jobs))

    spreads = {}
    for cid in REPEAT_CASES:
        scores = [r["result"].get("score") for r in runs if r["case"] == cid]
        nums = [s for s in scores if isinstance(s, (int, float))]
        spreads[cid] = {"scores": scores, "spread": (max(nums) - min(nums)) if nums else None}
    rep = [r for r in runs if r["case"] in REPEAT_CASES]
    summary = {
        "version": version,
        "date": datetime.now().isoformat(timespec="seconds"),
        "models": sorted({s["model"] for r in runs for s in r["result"].get("steps", [])}),
        "llm_calls": sum(len(r["result"].get("steps", [])) for r in runs),
        "scores_per_case": spreads,
        "avg_score_spread": round(sum(v["spread"] or 0 for v in spreads.values()) / len(spreads), 1),
        "repeat_runs_passing_checks": f"{sum(r['check']['passed'] for r in rep)}/{len(rep)}",
        "json_valid_runs": f"{sum(bool(r['result'].get('json_ok')) for r in runs)}/{len(runs)}",
        "cpp_counted_as_match_T01": f"{sum(any('c++' in n for n in r['check']['notes'] if 'match' in n) for r in runs if r['case']=='T01')}/{REPEATS}",
        "injection_T11": [r["result"].get("score") for r in runs if r["case"] == "T11"],
        "invalid_T13_flagged": [r["check"]["passed"] for r in runs if r["case"] == "T13"],
        "check_notes": {f"{r['case']}#{r['run']}": r["check"]["notes"] for r in runs},
    }
    out_dir = ROOT / "test-data/outputs/version_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{version}_runs.json").write_text(json.dumps(runs, indent=1, ensure_ascii=False))
    (out_dir / f"{version}_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    for v in sys.argv[1:] or ["v1", "v2", "v3", "v4", "v5"]:
        s = run_version(v)
        print(json.dumps({k: s[k] for k in s if k != "check_notes"}, ensure_ascii=False), flush=True)
