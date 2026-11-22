# Changelog

All changes since Milestone 1 (proposal submitted 9 October 2026).

## 2026-11-22
- Added the final 3-step prompt workflow: P1 Extractor, P2 Matcher, P3 Coach (`prompts/final/`).
- Saved earlier prompt versions: v1 baseline from Milestone 1, v2 single prompt with rubric and JSON, v3 first 3-step split, v4 with input validation and code-calculated score (`prompts/v1`-`v4`).
- v5 (final): P1 now quotes the strongest evidence for each skill and P2 uses the strongest matching skill, after v4 marked project-backed skills as only "listed".
- Switched the model from ChatGPT to Gemini 3.5 Flash-Lite (free API tier, so evaluators can test the app at no cost; Gemini 3.5 Flash allows only 20 free requests a day). LangChain's `ChatOpenAI` client is kept by using Gemini's OpenAI-compatible endpoint.
- Moved score calculation out of the prompt into code (`compute_score`), so the same statuses always give the same score.
- Added the evidence guard (drops quotes that are not in the resume) and the invented-skill check.
- Added input validation and prompt-injection detection to P1.
- Built the Streamlit web app with an Analyze tab, a Prompt Lab tab (v1 vs final) and sample inputs (`code/app.py`).
- Added 14 synthetic test cases (6 normal, 5 edge, 3 invalid) and scripts that run them and save outputs (`code/run_tests.py`, `code/compare_versions.py`).
- Added diagrams (`docs/diagrams/`) and the Milestone 2 PDF (`docs/`).
