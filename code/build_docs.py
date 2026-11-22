"""Builds docs/M2.html and docs/report.html from the real outputs; pdf.js prints them to PDF.
Edit docs/m2_config.json (links, Team ID, faculty) and rerun: python build_docs.py && node pdf.js"""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CFG = json.loads((DOCS / "m2_config.json").read_text())
CASES = json.loads((ROOT / "test-data/inputs/test_cases.json").read_text())
FINAL = {c["id"]: json.loads((ROOT / f"test-data/outputs/final/{c['id']}.json").read_text()) for c in CASES}
SUMM = {v: json.loads((ROOT / f"test-data/outputs/version_comparison/{v}_summary.json").read_text()) for v in ["v1", "v2", "v3", "v4", "v5"]}
TEXT = json.loads((DOCS / "m2_text.json").read_text())

e = html.escape


def img(path: Path, width="100%") -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" style="width:{width}">'


def table(headers, rows, cls="") -> str:
    h = "".join(f"<th>{e(x)}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def pre(text: str) -> str:
    return f"<pre>{e(text)}</pre>"


def prompt_parts(rel):
    t = (ROOT / "prompts" / rel).read_text()
    system = t.split("<!-- SYSTEM -->", 1)[1].split("<!-- USER -->", 1)[0].strip()
    user = t.split("<!-- USER -->", 1)[1].strip()
    return system, user


CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10.5pt; color: #1a1a1a; line-height: 1.42; }
h1 { font-size: 20pt; margin: 0 0 6px; } h2 { font-size: 15pt; border-bottom: 2px solid #1e3a8a; padding-bottom: 3px; margin-top: 0; color: #1e3a8a; }
h3 { font-size: 12pt; margin: 14px 0 6px; color: #1e3a8a; } h4 { font-size: 10.5pt; margin: 10px 0 4px; }
.section { page-break-before: always; } .cover { text-align: left; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 8.8pt; page-break-inside: auto; }
th, td { border: 1px solid #b8c0cc; padding: 4px 5px; vertical-align: top; text-align: left; }
th { background: #e8edf5; } tr { page-break-inside: avoid; }
pre { white-space: pre-wrap; word-break: break-word; font-family: 'Courier New', monospace; font-size: 7.9pt; background: #f6f7f9; border: 1px solid #dde1e6; padding: 6px 8px; margin: 4px 0 8px; }
.kv td:first-child { width: 28%; font-weight: bold; background: #f3f5f9; }
.pass { color: #166534; font-weight: bold; } .fail { color: #b91c1c; font-weight: bold; }
.caption { font-size: 9pt; color: #444; text-align: center; margin: 3px 0 12px; font-style: italic; }
.small { font-size: 9pt; color: #444; } .fig { text-align: center; margin: 8px 0; page-break-inside: avoid; }
.sheet { border: 1.5px solid #1e3a8a; padding: 8px 10px; margin: 10px 0 14px; }
"""


def cover() -> str:
    c = CFG
    members = "".join(f"<tr><td>{e(m['name'])}{' (Team leader)' if i == 0 else ''}</td><td>{e(m['enrollment'])}</td></tr>"
                      for i, m in enumerate(c["members"]))
    return f"""
<div class="cover">
<p class="small">SCSE4041 Prompt Engineering · Mini Project · Milestone 2</p>
<h1>{e(c['project_title'])}</h1>
<p style="font-size:12pt">Team <b>{e(c['team_name'])}</b> · Team ID <b>{e(c['team_id'])}</b></p>
<h2 style="margin-top:22px">1. Cover page</h2>
<table class="kv">
<tr><td>Team ID</td><td>{e(c['team_id'])}</td></tr>
<tr><td>Team name</td><td>{e(c['team_name'])}</td></tr>
<tr><td>Project title</td><td>{e(c['project_title'])}</td></tr>
<tr><td>Problem ID</td><td>{e(c['problem_id'])}</td></tr>
<tr><td>Batch</td><td>{e(c['batch'])}</td></tr>
<tr><td>Faculty name</td><td>{e(c['faculty'])}</td></tr>
<tr><td>Prototype link</td><td>{e(c['prototype_link'])}</td></tr>
<tr><td>Repository link</td><td>{e(c['repo_link'])}</td></tr>
<tr><td>Reel link</td><td>{e(c['reel_link'])} ({e(str(c['reel_seconds']))} seconds)</td></tr>
<tr><td>Main AI tool and model</td><td>Gemini 3.5 Flash-Lite (Google Gemini API) via LangChain, in a Streamlit web app</td></tr>
</table>
<h3>Team members</h3>
<table><thead><tr><th>Name</th><th>Enrollment no.</th></tr></thead><tbody>{members}</tbody></table>
<h3>Key numbers</h3>
<table class="kv">
<tr><td>Final prompts</td><td>{c['counts']['prompts']} (P1 Extractor, P2 Matcher, P3 Coach)</td></tr>
<tr><td>Test inputs</td><td>{c['counts']['tests']} (see Section 4)</td></tr>
<tr><td>Prompt versions</td><td>{c['counts']['versions']} (v1, v2, v3, v4, v5 = final; see Section 3)</td></tr>
</table>
</div>"""


def design() -> str:
    t = TEXT["design"]
    d = DOCS / "diagrams"
    figs = "".join(f'<div class="fig">{img(d / f, w)}<div class="caption">{e(cap)}</div></div>' for f, w, cap in [
        ("1_prompt_workflow.png", "52%", "Diagram 1: Prompt workflow. Blue = LLM prompt, yellow = plain code, green = output."),
        ("2_task_decomposition.png", "88%", "Diagram 2: Task decomposition into three sub-tasks handled by P1, P2 and P3."),
        ("3_input_output_flow.png", "66%", "Diagram 3: Input-output flow. Variables in {curly brackets} are the prompt variables."),
        ("4_system_architecture.png", "100%", "Diagram 4: System architecture of the deployed web app."),
    ])
    sheets = ""
    sample = FINAL["T01"]
    steps = {s["prompt"]: s for s in sample["output"]["steps"]}
    for pid, rel, meta in [("P1", "final/P1_extractor.md", t["sheets"]["P1"]), ("P2", "final/P2_matcher.md", t["sheets"]["P2"]),
                           ("P3", "final/P3_coach.md", t["sheets"]["P3"])]:
        system, user = prompt_parts(rel)
        out_text = steps[pid]["text"]
        if len(out_text) > 1800:
            out_text = out_text[:1800] + "\n... (shortened here; full output in test-data/outputs/final/T01.json)"
        var_rows = "".join(f"<tr><td>{{{e(k)}}}</td><td>{e(v)}</td></tr>" for k, v in meta["variables"].items())
        sheets += f"""
<div class="sheet">
<h4>Prompt {pid}: {e(meta['name'])}</h4>
<table class="kv">
<tr><td>Prompt ID and name</td><td>{pid} - {e(meta['name'])} (file prompts/{rel})</td></tr>
<tr><td>Step in the workflow</td><td>{e(meta['step'])}</td></tr>
<tr><td>Purpose</td><td>{e(meta['purpose'])}</td></tr>
<tr><td>Tool and model</td><td>Gemini 3.5 Flash-Lite (gemini-3.5-flash-lite) through LangChain ChatOpenAI, OpenAI-compatible endpoint</td></tr>
<tr><td>Settings</td><td>{e(meta['settings'])}</td></tr>
<tr><td>Number of examples</td><td>{e(meta['examples'])}</td></tr>
<tr><td>Output format</td><td>{e(meta['output'])}</td></tr>
</table>
<b>Full system prompt</b>{pre(system)}
<b>Full user prompt template</b>{pre(user)}
<b>Variables</b><table><thead><tr><th>Variable</th><th>What it holds</th></tr></thead><tbody>{var_rows}</tbody></table>
<b>Sample run (test T01, real input and actual output, model {e(steps[pid]['model'])}, {steps[pid]['seconds']} s)</b>
<p class="small">Input: the T01 resume (Alex Sharma) and job description shown in Section 4{', passed through the earlier steps' if pid != 'P1' else ''}.</p>
{pre(out_text)}
</div>"""
    return f"""<div class="section"><h2>2. Prompt and solution design</h2>
<h3>(a) Design summary</h3>{t['summary_html']}
<h3>(b) Diagrams</h3>{figs}
<h3>(c) Prompt sheets (one per final prompt)</h3>{sheets}</div>"""


def implementation() -> str:
    t = TEXT["implementation"]
    mods = table(["Module", "What it does", "Status", "Notes"], [[e(m[0]), e(m[1]), f"<b>{e(m[2])}</b>", e(m[3])] for m in t["modules"]])
    log = table(["Version", "What changed", "Why it was changed", "Result after the change (measured)"],
                [[f"<b>{e(r[0])}</b>", e(r[1]), e(r[2]), e(r[3])] for r in t["iteration_log"]])
    metric_rows = []
    for v in ["v1", "v2", "v3", "v4", "v5"]:
        s = SUMM[v]
        sc = s["scores_per_case"]
        metric_rows.append([v, ", ".join(s["models"]), str(s["llm_calls"]),
                            " / ".join(f"{k}: {sc[k]['scores']}" for k in sc), str(s["avg_score_spread"]),
                            s["repeat_runs_passing_checks"], s["json_valid_runs"], str(s["injection_T11"]),
                            "yes" if all(s["invalid_T13_flagged"]) else "no"])
    metrics = table(["Version", "Model", "LLM calls", "Scores over 3 runs (T01 / T04 / T05)", "Avg spread",
                     "Runs passing checks", "Strict JSON valid", "T11 injection score", "T13 recipe rejected"], metric_rows)
    texts = ""
    for label, files in [("v1 (baseline from Milestone 1)", ["v1/P0_baseline.md"]), ("v2", ["v2/P0_rubric_json.md"]),
                         ("v3", ["v3/P1_extractor.md", "v3/P2_matcher_scorer.md", "v3/P3_coach.md"]),
                         ("v4", ["v4/P1_extractor.md", "v4/P2_matcher.md", "v4/P3_coach.md"]),
                         ("v5 (final)", ["final/P1_extractor.md", "final/P2_matcher.md", "final/P3_coach.md"])]:
        texts += f"<h4>Full text of {e(label)}</h4>"
        for f in files:
            if label.startswith("v5"):
                texts += f'<p class="small">prompts/{f}: identical to the prompt sheet in Section 2(c).</p>'
                continue
            system, user = prompt_parts(f)
            texts += f'<p class="small"><b>prompts/{f}</b></p>' + pre(("SYSTEM:\n" + system + "\n\n" if system else "SYSTEM: none\n\n") + "USER:\n" + user)
    return f"""<div class="section"><h2>3. Implementation</h2>
<h3>What is built</h3>{t['built_html']}
<h3>Module status</h3>{mods}
<h3>Prompt iteration log</h3>
<p class="small">Every version was run on the same inputs: T01, T04 and T05 three times each (score consistency) plus T11 (prompt injection) and T13 (a recipe instead of a resume). The checks are the same as in the Section 4 test table. Raw outputs: test-data/outputs/version_comparison/.</p>
{log}
<h4>Measured numbers per version</h4>{metrics}<p class="small">v1 replies are free text, so only its score range and the C++ check could be applied; its 9/9 does not include the missing-skill checks that v2-v5 had to pass. LLM calls: v4 and v5 make 1 call for T13 because the input is rejected after P1.</p>
{texts}</div>"""


def testing() -> str:
    t = TEXT["testing"]
    rows = []
    for c in CASES:
        r = FINAL[c["id"]]
        res = r["output"]
        if res.get("valid") is False:
            actual = f"Rejected: {res.get('problem')}"
        else:
            st = lambda s: ", ".join(m["requirement"] for m in res.get("matches", []) if m.get("status") == s) or "-"
            actual = f"Score {res['score']}. Match: {st('match')}. Partial: {st('partial')}. Missing: {st('missing')}."
            if res.get("warnings"):
                actual += " Warning: " + " ".join(res["warnings"])
        ok = r["check"]["passed"] and c["id"] not in TEXT.get("manual_review", {})
        note = "" if r["check"]["passed"] else f" ({'; '.join(r['check']['notes'])})"
        if c["id"] in TEXT.get("manual_review", {}):
            note = " " + TEXT["manual_review"][c["id"]]
        rows.append([c["id"], e(c["title"]), c["type"], e(c["expected"]), e(actual) + f'<span class="small">{e(note)}</span>',
                     f'<span class="{"pass" if ok else "fail"}">{"Pass" if ok else "Fail"}</span>'])
    passed = sum(FINAL[c["id"]]["check"]["passed"] and c["id"] not in TEXT.get("manual_review", {}) for c in CASES)
    shots = "".join(f'<div class="fig">{img(ROOT / "docs/screenshots" / f, "92%")}<div class="caption">{e(cap)}</div></div>'
                    for f, cap in t["screenshots"])
    lim = table(["Limitation", "What we will try next (Milestone 3)"], [[e(a), e(b)] for a, b in t["limitations"]])
    return f"""<div class="section"><h2>4. Demonstration and testing</h2>
<h3>Test table</h3>
<p class="small">{len(CASES)} test inputs: {sum(c['type']=='Normal' for c in CASES)} normal, {sum(c['type']=='Edge' for c in CASES)} edge, {sum(c['type']=='Invalid' for c in CASES)} invalid. All run on the final workflow (v5), one run each. Pass/Fail is decided by the automated checks in test-data/inputs/test_cases.json (score range, requirements that must be flagged missing, skills that must not be counted), followed by a manual review of each output against its expected output. One test passed the automated checks but failed the manual review (T03). <b>Result: {passed} of {len(CASES)} passed.</b> Full inputs and outputs: test-data/.</p>
{table(["Test no.", "Input (short)", "Type", "Expected output", "Actual output (short)", "Pass / Fail"], rows)}
<h3>Screenshots of real runs</h3>{shots}
<h3>Known limitations</h3>{lim}</div>"""


def repository() -> str:
    t = TEXT["repository"]
    shot = ROOT / "docs/screenshots/repo.png"
    body = img(shot, "92%") if shot.exists() else "<p><b>[Repository screenshot goes here]</b></p>"
    items = "".join(f"<li>{e(x)}</li>" for x in t["changes"])
    return f"""<div class="section"><h2>5. Repository</h2>
<p>Repository: {e(CFG['repo_link'])}</p>
<div class="fig">{body}<div class="caption">Screenshot of the repository</div></div>
<h3>What changed since Milestone 1</h3><ul>{items}</ul></div>"""


def contribution() -> str:
    rows = [[e(m["name"]), e(m["enrollment"]), e(m["role"]), e(m["tasks"]), e(m["evidence"]), str(m["percent"])] for m in CFG["members"]]
    return f"""<div class="section"><h2>7. Team contribution</h2>
{table(["Member name", "Enrollment no.", "Role", "Tasks done in Milestone 2", "Evidence", "Contribution (%)"], rows)}
<p class="small">Total: {sum(m['percent'] for m in CFG['members'])}%. All members have agreed to this table.</p></div>"""


def report_body() -> str:
    return TEXT["report_html"]


def page(title, body) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{e(title)}</title><style>{CSS}</style></head><body>{body}</body></html>"


if __name__ == "__main__":
    report = report_body()
    (DOCS / "report.html").write_text(page("Technical report", report))
    m2 = cover() + design() + implementation() + testing() + repository() + \
        f'<div class="section"><h2>6. Supporting document</h2><p class="small">Type: Technical report. The same document is uploaded separately as {e(CFG["supporting_pdf_name"])}.</p>{report}</div>' + \
        contribution()
    (DOCS / "M2.html").write_text(page("Milestone 2", m2))
    print("built docs/M2.html and docs/report.html")
