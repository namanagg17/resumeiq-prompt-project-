"""Shared checks used by run_tests.py and compare_versions.py."""

from __future__ import annotations


def _low(s) -> str:
    return (s or "").lower()


def matched_names(result: dict) -> list[str]:
    """Requirement names the version treated as met (status match)."""
    if result.get("version") == "v1":
        return [_low(x) for x in result.get("matched_text", [])]
    return [_low(m.get("requirement")) for m in result.get("matches", []) if m.get("status") == "match"]


def missing_names(result: dict) -> list[str]:
    if result.get("version") == "v1":
        return []
    return [_low(m.get("requirement")) for m in result.get("matches", []) if m.get("status") == "missing"]


def check(case: dict, result: dict) -> dict:
    """Apply the test case's checks. Returns {"passed": bool, "notes": [...]}."""
    c = case.get("checks", {})
    notes = []
    if c.get("expect_invalid"):
        ok = result.get("valid") is False or result.get("score") is None
        notes.append("flagged as invalid" if ok else f"not flagged; gave score {result.get('score')}")
        return {"passed": ok, "notes": notes}

    passed = True
    if result.get("valid") is False:
        return {"passed": False, "notes": [f"wrongly rejected: {result.get('problem')}"]}
    score = result.get("score")
    lo, hi = c.get("score_range", [0, 100])
    if score is None or not (lo <= score <= hi):
        passed = False
        notes.append(f"score {score} outside {lo}-{hi}")
    for kw in c.get("must_not_match", []):
        if any(kw in name for name in matched_names(result)):
            passed = False
            notes.append(f"'{kw}' wrongly counted as a match")
    if result.get("version") != "v1":
        for kw in c.get("must_be_missing", []):
            if not any(kw in name for name in missing_names(result)):
                passed = False
                notes.append(f"'{kw}' not flagged as missing")
    if c.get("english_output"):
        text = " ".join([result.get("summary", "")] + [s.get("text", "") for s in result.get("suggestions", [])])
        hinglish = [w for w in ("maine", "banaya", "hai", "mein", "karta") if f" {w} " in f" {text.lower()} "]
        if hinglish:
            passed = False
            notes.append(f"Hinglish words in output: {hinglish}")
    return {"passed": passed, "notes": notes or ["all checks met"]}
