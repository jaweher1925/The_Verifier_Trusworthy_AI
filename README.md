# The Verifier — Hybrid RAG Hallucination Detector for Automotive Engineering

**Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering**
Jaweher Hichri, Samah Mansour — Grand Valley State University

The Verifier detects and corrects LLM-generated hallucinations in automotive engineering content (ISO 26262, AUTOSAR, VSS, OBD-II, ADAS, etc.) in real time. Paste any ChatGPT / Claude / Gemini output into the Chrome extension or the dashboard and get back, in under 2 seconds on a dedicated service tier:

- A **hallucination risk score** (0–100%)
- The **specific issues found**, each grounded in a cited automotive standard
- A **corrected version** anchored in the certified knowledge base
- **Live metrics** (ROUGE-L, accuracy, recall) updated after every verification

## Architecture — Seven-Stage Hybrid RAG Pipeline

1. **S1 — Local Pattern Layer**: 25 static rules + 7 context-aware regex checks catch invalid VSS paths, bogus ASILs, wrong OBD-II codes, and false CAN-bus claims in under 1 ms, with 100% precision on the rule set.
2. **S2 — TF-IDF Retrieval**: sparse cosine-similarity search over a 146-entry knowledge base, ~5 ms.
3. **S3 — RAG Judge**: an LLM judge (currently `gpt-oss-120b` on Groq; the same slot has also run LLaMA 3.3 70B) evaluates the input against retrieved standards and drafts a grounded repair, ~300–400 ms.
4. **S4 — Decision Fusion**: a deterministic S1 match always overrides the judge's probabilistic output.
5. **S5 — ROUGE-L Scoring**: measures lexical grounding of the generated correction against the knowledge base.
6. **S6/S7 — Persistence & Metrics**: every transaction is logged (SQLite) and surfaced on the live dashboard.

## Evaluation (300-case, cross-subdomain, standards-traced corpus)

Ground truth is fixed **by construction**, before any system run, eliminating the circularity of grading the system against its own risk score. Full methodology, confusion matrix, confidence intervals, per-subdomain breakdown, and ablation are in the paper (`paper/paper_camera.tex`).

| Metric | Full system (S1+S3) | Rules only (S1) |
|---|---|---|
| Accuracy (95% CI) | **0.840** (0.794–0.877) | 0.407 (0.353–0.463) |
| Precision | **0.972** | 1.000 |
| Recall (95% CI) | **0.761** (0.694–0.817) | 0.033 (0.015–0.069) |
| F1 score | **0.854** | 0.063 |

140 of 184 hallucinations detected, 4 false alarms. Mean end-to-end latency on a dedicated service tier: **1,259 ms**, within the 2-second real-time target.

> The live dashboard's running stats (from ad hoc demo inputs) are a separate, informal measurement — they are not the 300-case evaluation above.

## Repository Layout

- `backend/` — FastAPI server (`server.py`), knowledge base, index-build and utility scripts.
- `dashboard.py` — Streamlit live-metrics dashboard.
- `extension/` — Chrome extension (load unpacked from this folder).
- `evaluation/` — the formal 300-case benchmark: `evaluation_dataset.json` (labeled corpus), `run_evaluation.py` (evaluation script), and the saved `evaluation_results.json` matching the paper's results table.
- `paper/` — the camera-ready paper (`paper_camera.tex`) and figures.
- `presentation/` — conference and defense slide decks, speech scripts, and the test-case spreadsheet.

## Running the Live Demo (backend + dashboard + extension)

```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd backend
python build_index.py
python -m uvicorn server:app --port 8000
```

In a second terminal:

```bash
venv\Scripts\activate
streamlit run dashboard.py
```

Load the extension: `chrome://extensions` → enable Developer mode → "Load unpacked" → select the `extension/` folder.

Set `GROQ_API_KEY` and `JUDGE_MODEL` in `backend/.env` (see `.env.example`).

## Reproducing the 300-Case Evaluation

With the backend running on `:8000`:

```bash
cd evaluation
python run_evaluation.py --mode full
```

Expected result (already saved in `evaluation_results.json`): n=300, Accuracy 0.840, Precision 0.972, Recall 0.761, F1 0.854.
