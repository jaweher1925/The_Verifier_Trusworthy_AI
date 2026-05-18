# 🛡️ The Verifier v2.0 — Automotive AI Hallucination Detection

> **Master's Degree End-of-Year Project — 2026**
> Grand Valley State University Michigan | Leaders University Tunisia

---

## What Is This?

The Verifier detects and corrects hallucinations in LLM-generated automotive engineering content in real time. Paste any ChatGPT/Claude/Gemini output into the Chrome extension or dashboard and get back in under 2 seconds:

- A **hallucination score** (0–100%)
- A **list of issues** with severity (Critical / High / Medium)
- A **corrected version** grounded in verified automotive standards
- **Live metrics**: ROUGE-L, Accuracy, Recall — updated after every verification

---

## Final Results (38 live verifications)

| Metric | Value | Meaning |
|---|---|---|
| **ROUGE-L** | **0.232** | Correction word overlap with knowledge base — RAG grounding confirmed |
| **Accuracy** | **1.000** | All confident cases correctly classified |
| **Recall** | **1.000** | All hallucinations in confident set detected |
| High Risk detected | 15 / 38 (39.5%) | Correctly flagged as dangerous |
| Avg response time | 1649ms | Full pipeline including Groq API |
| Local detection only | < 5ms | Pattern detection, no internet needed |

---



## Architecture — Hybrid RAG Pipeline

```
User pastes text (Chrome Extension or Dashboard)
              ↓
Stage 1: Local Pattern Detection       25 patterns + 7 smart rules
              ↓
Stage 2: TF-IDF KB Search              cosine similarity, top 5 chunks
              ↓
Stage 3: Optional URL Context         user-provided extra source
              ↓
Stage 4: Groq LLaMA 3.3 70B           reads text + KB → corrected JSON
              ↓
Stage 5: Smart Score Decision         critical local patterns trusted
              ↓
Stage 6: ROUGE-L Computation          corrected vs relevant KB lines
              ↓
Stage 7: Save + Update Live Metrics    SQLite + evaluation update
              ↓
Response to extension/dashboard
```

---

## Project Structure

```
project/
├── backend/
│   ├── data/
│   │   └── knowledge_base.txt     ← 146 lines of verified automotive facts
│   ├── index/                     ← built by build_index.py
│   │   ├── vectorizer.pkl
│   │   ├── matrix.pkl
│   │   ├── chunks.pkl
│   │   └── sources.pkl
│   ├── build_index.py             ← run once to build TF-IDF index
│   ├── server.py                  ← FastAPI backend — all logic here
│   ├── fix_rouge.py               ← backfill ROUGE-L for existing history
│   └── history.db                 ← auto-created SQLite database
├── extension/
│   ├── manifest.json              ← Chrome Manifest V3
│   ├── popup.html / popup.js      ← extension UI with live metrics bar
│   ├── content.js                 ← captures selected text on webpages
│   ├── background.js              ← right-click context menu
│   └── icons/                    
├── dashboard.py                   ← Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## Knowledge Base Sources

| Source | File | Content |
|---|---|---|
| COVESA VSS 4.0 | knowledge_base.txt | Valid vs invalid signal paths |
| ISO 26262:2018 | knowledge_base.txt | ASIL A-D, HARA, Part 6 clauses 1-13, ABS 50-150ms |
| SOTIF ISO 21448 | knowledge_base.txt | Different from ISO 26262, requires validation |
| CAN Bus / OBD-II | knowledge_base.txt | 0x7DF broadcast, 0x7E8-0x7EF responses, no built-in security |
| AUTOSAR R22-11 | knowledge_base.txt | Classic vs Adaptive, ara::com is Adaptive only |
| HaluEval Patterns | knowledge_base.txt | Linguistic hallucination signatures |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/verify` | Full RAG pipeline — returns score, issues, corrected text, ROUGE-L |
| POST | `/reverify` | Re-verify corrected text — computes hallucination delta |
| GET | `/rouge` | Last saved ROUGE-L, Accuracy, Recall from evaluation |
| GET | `/history` | Past verification records |
| GET | `/stats` | Total, avg score, high risk count, avg speed |
| GET | `/live_metrics` | ROUGE-L per verification for chart |
| GET | `/health` | Server status, Groq connection, chunk count |
| GET | `/docs` | Swagger UI |

---

## How to Run

### Step 1 — Install dependencies
```bash
pip install fastapi uvicorn groq scikit-learn numpy python-dotenv streamlit requests
```

### Step 2 — Add Groq API key
Get a free key at https://console.groq.com (no credit card)

```bash
cd backend
echo GROQ_API_KEY=gsk_your_key_here > .env
```

### Step 3 — Build the knowledge base index (once only)
```bash
python build_index.py
```

### Step 4 — Start backend (Terminal 1)
```bash
python server.py
```
Check: http://localhost:8000/health → should show `"groq": true`

### Step 5 — Start dashboard (Terminal 2)
```bash
cd ..
```
```bash 
### Installer Streamlit 
```
streamlit run dashboard.py
python -m streamlit run dashboard.py
```
Opens at: http://localhost:PORT

### Step 6 — Load Chrome Extension
```
chrome://extensions/ → Developer mode ON → Load unpacked → select extension/ folder
```

### Step 7 — Backfill ROUGE-L (if you have existing history)
```bash
cd backend
python fix_rouge.py
```

---


## Evaluation Metrics

| Metric | Definition | Value |
|---|---|---|
| ROUGE-L | Word overlap between correction and KB (Ji et al. 2022) | 0.232 |
| Accuracy | Correct classifications / total confident cases | 1.000 |
| Recall | Hallucinations caught / total actual hallucinations | 1.000 |

Metrics update automatically after every verification — no button needed.

---

## MLOps

| Tool | Role |
|---|---|
| Git | Version control — tags v1.0, v2.0 |
| DVC | Knowledge base versioning |
| Docker | Portable container |
| Streamlit | Live monitoring dashboard |

---

## References

1. Ji et al. (2022). Survey of hallucination in NLG. ACM Computing Surveys.
2. Huang et al. (2024). Survey on hallucination in large language models.
3. Pavel et al. (2025). Knowledge Conflation Hallucination in Automotive LLM.
4. Li et al. (2023). HaluEval: Hallucination evaluation benchmark. EMNLP 2023.
5. Wunnava et al. (2025). RAG-enhanced automotive compliance verification.
6. Mahawatta Dona et al. (2024). Hallucination detection in automotive AI.
7. Khati et al. (2024). LLM hallucination in safety-critical domains.
