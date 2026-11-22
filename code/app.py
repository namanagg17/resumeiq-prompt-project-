"""ResumeIQ web app (Streamlit). Run: streamlit run code/app.py"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import resumeiq

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = json.loads((ROOT / "test-data/inputs/test_cases.json").read_text())

st.set_page_config(page_title="ResumeIQ", page_icon="📄", layout="wide")
st.title("📄 ResumeIQ")
st.caption("Compare a resume with a job description: evidence-based match score, skill gaps and honest suggestions. "
           "Powered by Gemini 3.5 Flash-Lite through a 3-step LangChain prompt workflow.")

with st.sidebar:
    st.subheader("Try a sample")
    options = ["(type your own)"] + [f"{c['id']} - {c['title']}" for c in SAMPLES]
    pick = st.selectbox("Sample input", options)
    if st.button("Load sample", use_container_width=True) and pick != options[0]:
        case = SAMPLES[options.index(pick) - 1]
        st.session_state["resume"] = case["resume"]
        st.session_state["jd"] = case["jd"]
    st.divider()
    st.markdown("**Workflow**\n1. P1 checks the input and extracts skills with exact quotes\n"
                "2. Code removes any quote not found in the resume\n3. P2 matches each requirement\n"
                "4. Code calculates the score (75% must-have, 25% good-to-have)\n5. P3 writes honest suggestions")
    st.caption("Use made-up or anonymised resumes. Nothing you paste is stored.")

col1, col2 = st.columns(2)
resume = col1.text_area("Resume text", key="resume", height=260, placeholder="Paste the resume here")
jd = col2.text_area("Job description", key="jd", height=260, placeholder="Paste the job description here")

tab_analyze, tab_lab = st.tabs(["Analyze", "Prompt Lab: v1 vs final"])

STATUS_ICON = {"match": "✅ Match", "partial": "🟡 Partial", "missing": "❌ Missing"}


def show_final(res: dict):
    if res.get("valid") is False:
        st.error(f"Input problem: {res.get('problem')}")
        return
    for w in res.get("warnings", []):
        st.warning(w)
    a, b = st.columns([1, 3])
    a.metric("Match score (out of 100)", res["score"])
    a.caption("Calculated by code from the statuses: 75% must-have, 25% good-to-have.")
    b.info(res.get("summary", ""))
    st.subheader("Requirement by requirement")
    st.dataframe(
        [{"Requirement": m.get("requirement"), "Priority": "Must-have" if m.get("priority") == "must" else "Good-to-have",
          "Status": STATUS_ICON.get(m.get("status"), m.get("status")), "Evidence from resume": m.get("evidence") or "-",
          "Reason": m.get("reason", "")} for m in res.get("matches", [])],
        use_container_width=True, hide_index=True)
    st.subheader("Suggestions")
    for i, s in enumerate(res.get("suggestions", []), 1):
        st.markdown(f"**{i}. [{s.get('type')}]** {s.get('text')}  \n<small>Requirement: {s.get('related_requirement', '-')}</small>",
                    unsafe_allow_html=True)
    if res.get("rewritten_lines"):
        st.subheader("Rewritten lines (same facts, clearer wording)")
        for r in res["rewritten_lines"]:
            st.markdown(f"- ~~{r.get('original')}~~  \n  → {r.get('improved')}")
    with st.expander("Behind the scenes: each prompt step"):
        for s in res.get("steps", []):
            st.markdown(f"**{s['prompt']}** · {s['model']} · {s['seconds']} s")
            st.code(s["text"][:3000], language="json")


with tab_analyze:
    if st.button("Analyze resume", type="primary"):
        with st.spinner("Running P1 → P2 → P3 (about 20 seconds)..."):
            try:
                st.session_state["final"] = resumeiq.run_final(resume, jd)
            except Exception as err:
                st.error(f"The model call failed: {err}. Please try again in a minute.")
    if "final" in st.session_state:
        show_final(st.session_state["final"])

with tab_lab:
    st.write("Runs the **v1 baseline prompt** from Milestone 1 and the **final workflow** on the same input, "
             "so you can see what prompt engineering changed.")
    if st.button("Run both versions"):
        with st.spinner("Running v1 and the final workflow..."):
            try:
                st.session_state["lab_v1"] = resumeiq.run_v1(resume, jd)
                st.session_state["lab_final"] = resumeiq.run_final(resume, jd)
            except Exception as err:
                st.error(f"The model call failed: {err}")
    if "lab_v1" in st.session_state:
        left, right = st.columns(2)
        with left:
            st.markdown("#### v1 baseline (one free-text prompt)")
            st.markdown(st.session_state["lab_v1"]["raw"])
        with right:
            st.markdown("#### Final (P1 → guard → P2 → score → P3)")
            show_final(st.session_state["lab_final"])
