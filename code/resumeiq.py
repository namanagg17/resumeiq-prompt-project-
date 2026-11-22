"""ResumeIQ core: prompt loading, Gemini calls through LangChain, the 3-step workflow,
the evidence guard and the score calculation. Used by app.py and the test scripts."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"

# Gemini's OpenAI-compatible endpoint, so LangChain's ChatOpenAI client works unchanged.
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.1-flash-lite"  # used only if the primary is overloaded or rate-limited


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st

            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            key = None
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set (environment variable or Streamlit secret).")
    return key


# ---------------------------------------------------------------- prompts
def load_prompt(rel_path: str) -> dict:
    """Read a prompt file: text after <!-- SYSTEM --> and <!-- USER --> markers."""
    text = (PROMPTS / rel_path).read_text(encoding="utf-8")
    system = text.split("<!-- SYSTEM -->", 1)[1].split("<!-- USER -->", 1)[0].strip()
    user = text.split("<!-- USER -->", 1)[1].strip()
    return {"system": system, "user": user}


def fill(template: str, **values: str) -> str:
    """Replace only the named {variables}; JSON braces in the prompt stay untouched."""
    for name, value in values.items():
        template = template.replace("{" + name + "}", value)
    return template


# ---------------------------------------------------------------- LLM call
def call_llm(system: str, user: str, temperature: float | None = None, json_mode: bool = False,
             model: str = PRIMARY_MODEL, retries: int = 7) -> dict:
    """One LLM call. Returns {"text", "model", "seconds"}. Retries on overload/rate limits."""
    messages = ([SystemMessage(system)] if system else []) + [HumanMessage(user)]
    kwargs = {"model": model, "base_url": BASE_URL, "api_key": _api_key(), "max_retries": 0, "timeout": 120}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    last_err = None
    for attempt in range(retries):
        use_model = model if attempt < retries - 2 else FALLBACK_MODEL
        kwargs["model"] = use_model
        try:
            start = time.time()
            reply = ChatOpenAI(**kwargs).invoke(messages)
            return {"text": reply.content if isinstance(reply.content, str) else str(reply.content),
                    "model": use_model, "seconds": round(time.time() - start, 1)}
        except Exception as err:  # 429 / 503 / timeouts
            last_err = err
            time.sleep(min(4 * 2 ** attempt, 30))
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_err}")


def parse_json(text: str):
    """Strict JSON parse; returns None when the model broke the format."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        return None  # markdown fences count as a format break
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def parse_json_lenient(text: str):
    """Pull the first {...} block out of a reply (used to still score broken replies)."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- guard + score (no LLM)
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def verify_evidence(skills: list, resume: str):
    """Keep only skills whose evidence quote really appears in the resume."""
    resume_n = _norm(resume)
    kept, dropped = [], []
    for s in skills or []:
        ev = _norm(s.get("evidence", ""))
        (kept if ev and ev in resume_n else dropped).append(s)
    return kept, dropped


STATUS_VALUE = {"match": 1.0, "partial": 0.5, "missing": 0.0}


def compute_score(matches: list) -> int:
    """75% weight on must-have requirements, 25% on good-to-have ones."""
    must = [STATUS_VALUE.get(m.get("status"), 0) for m in matches if m.get("priority") == "must"]
    nice = [STATUS_VALUE.get(m.get("status"), 0) for m in matches if m.get("priority") != "must"]
    if not must and not nice:
        return 0
    if not nice:
        return round(100 * sum(must) / len(must))
    if not must:
        return round(100 * sum(nice) / len(nice))
    return round(75 * sum(must) / len(must) + 25 * sum(nice) / len(nice))


def check_invented_skills(rewritten: list, matches: list, resume: str) -> list:
    """Flag rewritten lines that mention a missing requirement the resume never mentions."""
    resume_n = _norm(resume)
    flags = []
    for line in rewritten or []:
        improved = _norm(line.get("improved", ""))
        for m in matches or []:
            if m.get("status") != "missing":
                continue
            key = _norm(m.get("requirement", ""))
            if key and len(key) <= 30 and key in improved and key not in resume_n:
                flags.append(f"Rewritten line mentions '{m['requirement']}', which is not in the resume.")
    return flags


def basic_input_check(resume: str, jd: str) -> str | None:
    """Cheap check before spending an LLM call."""
    if len((resume or "").split()) < 3:
        return "The resume is empty or too short. Paste the full resume text."
    if len((jd or "").split()) < 3:
        return "The job description is empty or too short. Paste the full job description."
    return None


# ---------------------------------------------------------------- final workflow (v5; v4 = same code, prompts/v4)
def run_final(resume: str, jd: str, folder: str = "final") -> dict:
    out = {"version": "v5-final" if folder == "final" else folder, "steps": [], "warnings": []}
    problem = basic_input_check(resume, jd)
    if problem:
        out.update(valid=False, problem=problem)
        return out

    # Step 1: input check + extraction
    p1 = load_prompt(f"{folder}/P1_extractor.md")
    r1 = call_llm(p1["system"], fill(p1["user"], resume=resume, jd=jd), temperature=0.2, json_mode=True)
    d1 = parse_json(r1["text"]) or parse_json_lenient(r1["text"]) or {}
    out["steps"].append({"prompt": "P1", **r1})
    check = d1.get("input_check", {})
    if not check.get("resume_valid", True) or not check.get("jd_valid", True):
        out.update(valid=False, problem=check.get("problem") or "The input does not look like a resume and job description.",
                   json_ok=parse_json(r1["text"]) is not None)
        return out
    if d1.get("injection_detected"):
        out["warnings"].append("The resume contains instructions aimed at the AI. They were ignored.")

    # Guard: drop skills whose evidence is not really in the resume
    skills, dropped = verify_evidence(d1.get("candidate_skills", []), resume)
    for s in dropped:
        out["warnings"].append(f"Removed '{s.get('skill')}': its evidence quote was not found in the resume.")
    reqs = d1.get("jd_requirements", [])

    # Step 2: requirement matching
    p2 = load_prompt(f"{folder}/P2_matcher.md")
    r2 = call_llm(p2["system"], fill(p2["user"], candidate_skills=json.dumps(skills, ensure_ascii=False),
                                     jd_requirements=json.dumps(reqs, ensure_ascii=False)),
                  temperature=0.2, json_mode=True)
    d2 = parse_json(r2["text"]) or parse_json_lenient(r2["text"]) or {}
    out["steps"].append({"prompt": "P2", **r2})
    matches = d2.get("matches", [])

    # Step 3: improvement suggestions
    p3 = load_prompt(f"{folder}/P3_coach.md")
    r3 = call_llm(p3["system"], fill(p3["user"], resume=resume, matches=json.dumps(matches, ensure_ascii=False)),
                  temperature=0.4, json_mode=True)
    d3 = parse_json(r3["text"]) or parse_json_lenient(r3["text"]) or {}
    out["steps"].append({"prompt": "P3", **r3})
    out["warnings"] += check_invented_skills(d3.get("rewritten_lines", []), matches, resume)

    out.update(valid=True, score=compute_score(matches), matches=matches, summary=d2.get("summary", ""),
               candidate_skills=skills, suggestions=d3.get("suggestions", []),
               rewritten_lines=d3.get("rewritten_lines", []),
               json_ok=all(parse_json(s["text"]) is not None for s in out["steps"]))
    return out


# ---------------------------------------------------------------- older versions (for the iteration log)
def run_v1(resume: str, jd: str) -> dict:
    p = load_prompt("v1/P0_baseline.md")
    r = call_llm(p["system"], fill(p["user"], resume=resume, jd=jd))
    text = r["text"]
    m = re.search(r"(\d{1,3})\s*(?:/|out of)\s*100", text)
    # free text: pull the "Matching Skills" section as the list of matched items
    sec = re.search(r"match\w*\s*skills?[^\n]*\n(.*?)(?:\n\s*\n\s*[#*]|\n#+|\Z)", text, re.I | re.S)
    matched = [re.sub(r"^[\s*\-•\d.]+", "", ln).strip("* ").strip() for ln in (sec.group(1).splitlines() if sec else [])]
    return {"version": "v1", "steps": [{"prompt": "P0", **r}], "valid": True, "raw": text,
            "score": int(m.group(1)) if m else None, "matched_text": [x for x in matched if x], "json_ok": False}


def run_v2(resume: str, jd: str) -> dict:
    p = load_prompt("v2/P0_rubric_json.md")
    r = call_llm(p["system"], fill(p["user"], resume=resume, jd=jd))
    strict = parse_json(r["text"])
    d = strict or parse_json_lenient(r["text"]) or {}
    return {"version": "v2", "steps": [{"prompt": "P0", **r}], "valid": True, "raw": r["text"],
            "score": d.get("score"), "matches": d.get("matches", []), "json_ok": strict is not None}


def run_v3(resume: str, jd: str) -> dict:
    out = {"version": "v3", "steps": [], "valid": True}
    p1 = load_prompt("v3/P1_extractor.md")
    r1 = call_llm(p1["system"], fill(p1["user"], resume=resume, jd=jd), temperature=0.2, json_mode=True)
    d1 = parse_json(r1["text"]) or parse_json_lenient(r1["text"]) or {}
    p2 = load_prompt("v3/P2_matcher_scorer.md")
    r2 = call_llm(p2["system"], fill(p2["user"], candidate_skills=json.dumps(d1.get("candidate_skills", [])),
                                     jd_requirements=json.dumps(d1.get("jd_requirements", []))),
                  temperature=0.2, json_mode=True)
    d2 = parse_json(r2["text"]) or parse_json_lenient(r2["text"]) or {}
    p3 = load_prompt("v3/P3_coach.md")
    r3 = call_llm(p3["system"], fill(p3["user"], resume=resume, matches=json.dumps(d2.get("matches", []))),
                  temperature=0.4, json_mode=True)
    d3 = parse_json(r3["text"]) or parse_json_lenient(r3["text"]) or {}
    out["steps"] = [{"prompt": "P1", **r1}, {"prompt": "P2", **r2}, {"prompt": "P3", **r3}]
    _, dropped = verify_evidence(d1.get("candidate_skills", []), resume)
    out.update(score=d2.get("score"), matches=d2.get("matches", []), summary=d2.get("summary", ""),
               suggestions=d3.get("suggestions", []), rewritten_lines=d3.get("rewritten_lines", []),
               unverified_evidence=len(dropped),
               json_ok=all(parse_json(s["text"]) is not None for s in out["steps"]))
    return out


RUNNERS = {"v1": run_v1, "v2": run_v2, "v3": run_v3, "v4": lambda r, j: run_final(r, j, folder="v4"), "v5": run_final}
