# ResumeIQ: AI-Powered Resume Analysis and Job Matching Assistant

SCSE4041 Prompt Engineering mini project, Bennett University. Team **Naman square** (Team ID PE-B01-06). Problem pool ID: C9.

ResumeIQ compares a student's resume with a job description and returns:
- a **match score out of 100**, calculated by code from per-requirement statuses (not guessed by the model)
- a **requirement-by-requirement table** (match / partial / missing), each match backed by an exact quote from the resume
- **3-5 honest suggestions** and up to 3 rewritten resume lines that never invent skills or numbers
- **warnings** for prompt injection, unverifiable quotes and invented skills; invalid inputs are rejected

**Prototype:** PROTOTYPE_LINK

## How it works
| Step | What runs | Model / settings |
|---|---|---|
| 0 | Basic input check (code) | - |
| 1 | **P1 Extractor** (`prompts/final/P1_extractor.md`): input validity, injection flag, skills with exact quotes, JD requirements | Gemini 3.5 Flash-Lite, temp 0.2, JSON mode |
| 2 | Evidence guard (code): drops any quote that is not in the resume | - |
| 3 | **P2 Matcher** (`prompts/final/P2_matcher.md`): status per requirement, 1 worked example | Gemini 3.5 Flash-Lite, temp 0.2, JSON mode |
| 4 | Score (code): 75% must-have + 25% good-to-have; match 1, partial 0.5, missing 0 | - |
| 5 | **P3 Coach** (`prompts/final/P3_coach.md`): suggestions + rewritten lines | Gemini 3.5 Flash-Lite, temp 0.4, JSON mode |
| 6 | Invented-skill check (code) | - |

Gemini is called through LangChain's `ChatOpenAI` client using Gemini's OpenAI-compatible endpoint. If `gemini-3.5-flash-lite` is overloaded, the last retry uses `gemini-3.1-flash-lite`.

## Run it yourself
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here   # free key: https://aistudio.google.com/apikey
streamlit run code/app.py
```
Run the 14 test cases: `cd code && python run_tests.py` (outputs go to `test-data/outputs/final/`).
Compare prompt versions v1-v5: `cd code && python compare_versions.py` (outputs go to `test-data/outputs/version_comparison/`).

## Folder structure
```
prompts/v1 ... v4/    older prompt versions (one file per prompt)
prompts/final/        final prompts P1, P2, P3
code/                 app.py (Streamlit UI), resumeiq.py (workflow), evaluate.py, run_tests.py, compare_versions.py
test-data/inputs/     test_cases.json (14 synthetic resume + JD pairs)
test-data/outputs/    saved outputs of every test run and version comparison
docs/                 diagrams and the Milestone 2 PDF
CHANGELOG.md          dated changes since Milestone 1
```

## Privacy
All resumes in `test-data/` are made up. The app stores nothing. No API key is in this repository: the key is read from the `GEMINI_API_KEY` environment variable or a Streamlit secret.

## Team
| Enrollment no. | Name | Main task |
|---|---|---|
| S24CSEU0607 | Naman Aggarwal (leader) | Wrote prompts P1, P2, P3 and versions v1-v5; designed the scoring rubric; ran the version comparison and wrote the iteration log |
| S24CSEU0605 | Naman Agarwal | Built the Streamlit app and LangChain workflow code; wrote the 14 test cases and test runner; made the diagrams and reel |
