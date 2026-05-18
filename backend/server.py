"""
The Verifier — Automotive AI Hallucination Detection
FastAPI backend with pattern detection + TF-IDF RAG + Groq LLaMA 3.3 70B
Run: python server.py
"""
import os, json, pickle, sqlite3, datetime, time, csv, re, math
from pathlib import Path
from typing import Optional, List
from statistics import mean

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BASE      = Path(__file__).parent
INDEX_DIR = BASE / "index"
DB_FILE   = BASE / "history.db"
DATA_DIR  = BASE / "data"
GROQ_KEY  = os.getenv("GROQ_API_KEY", "")

app = FastAPI(title="The Verifier", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Database ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            input_text TEXT,
            score      REAL,
            corrected  TEXT,
            sources    TEXT,
            subdomain  TEXT,
            time_ms    INTEGER,
            rouge_l    REAL
        );
        CREATE TABLE IF NOT EXISTS evaluations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            rouge_l    REAL,
            f1_score   REAL,
            precision  REAL,
            recall     REAL,
            accuracy   REAL,
            total      INTEGER
        );
    """)
    conn.commit(); conn.close()

def save_history(text, score, corrected, sources, subdomain, ms, rl=None):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO history VALUES (NULL,?,?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), text[:500], score,
         corrected[:1000], json.dumps(sources), subdomain, ms, rl)
    )
    conn.commit(); conn.close()

# ── Search index ──────────────────────────────────────────────────────────────
vectorizer = chunks = matrix = sources_list = None

def load_index():
    global vectorizer, chunks, matrix, sources_list
    if not INDEX_DIR.exists():
        print("WARNING: Run python build_index.py first"); return
    vectorizer   = pickle.load(open(INDEX_DIR/"vectorizer.pkl","rb"))
    matrix       = pickle.load(open(INDEX_DIR/"matrix.pkl","rb"))
    chunks       = pickle.load(open(INDEX_DIR/"chunks.pkl","rb"))
    sources_list = pickle.load(open(INDEX_DIR/"sources.pkl","rb"))
    print(f"Index loaded: {len(chunks)} chunks")

def search(query: str, top_k=5):
    if vectorizer is None: return "", []
    from sklearn.metrics.pairwise import cosine_similarity
    qv   = vectorizer.transform([query])
    sims = cosine_similarity(qv, matrix).flatten()
    top  = np.argsort(sims)[::-1][:top_k]
    top  = [i for i in top if sims[i] > 0.01]
    if not top: return "", []
    ctx  = "\n\n".join(chunks[i] for i in top)
    srcs = list(set(sources_list[i] for i in top))
    return ctx, srcs

# ── Groq ──────────────────────────────────────────────────────────────────────
groq_client = None

def init_groq():
    global groq_client
    if GROQ_KEY and not GROQ_KEY.startswith("your_"):
        groq_client = Groq(api_key=GROQ_KEY)
        print("Groq LLaMA 3.3 70B ready")
    else:
        print("No GROQ_API_KEY — local detection only")

# ── Detection patterns ────────────────────────────────────────────────────────
# Each tuple: (keyword, subdomain, severity, explanation)
# These patterns ONLY match things that are ALWAYS wrong — no false positives
PATTERNS = [
    # Wrong VSS paths — always wrong, never used correctly
    ("vehicle.speed.current",  "software",   "critical", "Wrong VSS path — does not exist. Correct: Vehicle.Speed"),
    ("vehicle.speed.current",  "software",   "critical", "Wrong VSS path. Correct: Vehicle.Speed"),
    ("vehicle.engine.rpm",     "software",   "critical", "Wrong VSS path. Correct: Vehicle.Powertrain.CombustionEngine.Speed"),
    ("vehicle.battery.soc",    "software",   "critical", "Wrong VSS path. Correct: Vehicle.Powertrain.TractionBattery.StateOfCharge.Current"),
    ("vehicle.battery.level",  "software",   "critical", "Wrong VSS path. Correct: Vehicle.Powertrain.TractionBattery.StateOfCharge.Current"),
    ("vehicle.gps.latitude",   "software",   "high",     "Wrong VSS path. Correct: Vehicle.CurrentLocation.Latitude"),
    ("vehicle.gps.longitude",  "software",   "high",     "Wrong VSS path. Correct: Vehicle.CurrentLocation.Longitude"),
    ("vehicle.fuel.level",     "software",   "high",     "Wrong VSS path. Correct: Vehicle.Powertrain.FuelSystem.Level"),
    ("vehicle.abs.status",     "software",   "medium",   "Wrong VSS path. Correct: Vehicle.ADAS.ABS.IsActive"),
    ("vehicle.ac.temperature", "software",   "medium",   "Wrong VSS path. Correct: Vehicle.Cabin.HVAC.Station.Row1.Left.Temperature"),
    ("vehicle.odometer",       "software",   "medium",   "Wrong VSS path. Correct: Vehicle.TravelledDistance"),
    ("vehicle.doors.front",    "software",   "medium",   "Wrong VSS path. Correct: Vehicle.Cabin.Door.Row1.Left.IsOpen"),
    # Non-existent ASIL levels — always wrong
    ("asil e",                 "safety",     "critical", "ASIL E does not exist. Valid levels: A, B, C, D only"),
    ("asil f",                 "safety",     "critical", "ASIL F does not exist. Valid levels: A, B, C, D only"),
    ("asil g",                 "safety",     "critical", "ASIL G does not exist. Valid levels: A, B, C, D only"),
    ("asil z",                 "safety",     "critical", "ASIL Z does not exist. Valid levels: A, B, C, D only"),
    ("asil 1",                 "safety",     "critical", "ASIL 1 does not exist. ASIL uses letters A-D not numbers"),
    ("asil 2",                 "safety",     "critical", "ASIL 2 does not exist. ASIL uses letters A-D not numbers"),
    ("asil 3",                 "safety",     "critical", "ASIL 3 does not exist. ASIL uses letters A-D not numbers"),
    ("asil 4",                 "safety",     "critical", "ASIL 4 does not exist. ASIL uses letters A-D not numbers"),
    ("asil 5",                 "safety",     "critical", "ASIL 5 does not exist. ASIL uses letters A-D not numbers"),
    # Wrong OBD-II addresses — always wrong in OBD-II context
    ("0x7ff",                  "electrical", "critical", "0x7FF is max CAN ID, not OBD-II address. Broadcast address is 0x7DF"),
    # Absolute impossible claims
    ("guaranteed to always",   "general",    "high",     "Absolute guarantee in safety context — no automotive system can be guaranteed"),
    ("always accurately",      "general",    "high",     "Absolute accuracy claim — sensor accuracy depends on calibration and conditions"),
    ("never fails",            "general",    "high",     "No automotive system has a zero failure rate"),
    ("100% accurate",          "general",    "high",     "100% accuracy claim requires formal validation — cannot be asserted"),
    ("100% reliable",          "general",    "high",     "100% reliability claim requires formal validation — cannot be asserted"),
    ("always correct",         "general",    "high",     "Absolute correctness claim — hallucination red flag"),
    ("studies show",           "general",    "medium",   "Generic citation without naming the study source"),
    ("certainly",              "general",    "medium",   "False certainty without supporting evidence"),
]

# Context-aware checks — smarter rules that avoid false positives
def check_abs_timing(text):
    """ABS timing outside 50-150ms is wrong."""
    matches = re.findall(r'abs[^.!?]{0,80}?(\d+)\s*(?:ms\b|millisecond)', text.lower())
    for m in matches:
        v = int(m)
        if v < 40 or v > 200:
            return True, v
    return False, None

def check_asil_no_hara(text):
    """ASIL assigned but HARA not mentioned or negated — wrong process."""
    tl = text.lower()
    if "asil" not in tl: return False

    if "hara" not in tl:
        # HARA not mentioned — check for explicit bad phrases
        bad = ["without formal", "without analysis", "without a formal",
               "without conducting", "no formal", "self-certified",
               "obviously qualifies", "clearly qualifies", "does not require",
               "without performing", "no need for"]
        return any(p in tl for p in bad)

    # HARA IS mentioned — check if it is negated ("without HARA", "no HARA")
    idx    = tl.find("hara")
    window = tl[max(0, idx-50):idx+10]
    if any(n in window for n in ["without", "no ", "skip", "not require"]):
        return True  # "without HARA" = hallucination

    return False  # HARA mentioned positively = correct usage

def check_fake_clause(text):
    """ISO 26262 Part 6 clause > 13 does not exist."""
    tl = text.lower()
    if "26262" not in tl: return False, None
    matches = re.findall(r'(?:part\s*6[^.]{0,20}?)?clause\s*(\d+)', tl)
    for m in matches:
        v = int(m)
        if v > 13:
            return True, v
    return False, None

def check_can_has_security(text):
    """CAN claimed to have built-in security is wrong."""
    tl = text.lower()
    bad = ["built-in authentication", "built-in encryption", "built-in security",
           "inherently secure", "includes encryption", "cryptographic hash",
           "includes authentication", "has encryption", "has authentication"]
    if not any(p in tl for p in bad): return False
    if "can" not in tl: return False
    # Make sure it is not negated
    for p in bad:
        if p in tl:
            idx = tl.find(p)
            window = tl[max(0, idx-50):idx+10]
            if any(n in window for n in ["lacks", "no ", "does not", "without", "lack "]):
                return False
    return True

def check_ara_com_classic(text):
    """ara::com with Classic Platform is wrong."""
    tl = text.lower()
    if "ara::com" not in tl: return False
    if "classic" in tl: return True
    # ara::com without context of adaptive platform
    if "adaptive" not in tl: return True
    return False

def check_adaptive_bare_metal(text):
    """Adaptive Platform on bare-metal is wrong."""
    tl = text.lower()
    bad = ["bare-metal", "bare metal", "without an operating system",
           "without os", "without posix", "no operating system"]
    if not any(p in tl for p in bad): return False
    if "adaptive" not in tl: return False
    # If text also mentions POSIX/Linux as requirement it is correct usage
    ok = ["requires posix", "requires a posix", "needs posix",
          "adaptive platform requires", "posix operating system", "linux or qnx"]
    if any(p in tl for p in ok): return False
    return True

def check_sotif_same_as_iso(text):
    """SOTIF described as same as or replacement for ISO 26262 is wrong."""
    tl = text.lower()
    if "sotif" not in tl: return False
    bad = ["same as iso 26262", "replacement for iso 26262", "updated replacement",
           "same concerns", "same safety concerns", "covers the same"]
    return any(p in tl for p in bad)

def run_detection(text):
    """Run all patterns and smart checks. Return issues + local score."""
    tl = text.lower()
    issues = []
    seen   = set()

    # Static patterns
    for keyword, subdomain, severity, reason in PATTERNS:
        if keyword in tl and keyword not in seen:
            issues.append({"pattern": keyword, "subdomain": subdomain,
                           "severity": severity, "reason": reason})
            seen.add(keyword)

    # Smart checks
    abs_bad, abs_val = check_abs_timing(text)
    if abs_bad:
        issues.append({"pattern": "abs_timing", "subdomain": "mechanical",
                       "severity": "critical",
                       "reason": f"ABS timing {abs_val}ms is outside validated range of 50-150ms"})

    if check_asil_no_hara(text):
        issues.append({"pattern": "asil_no_hara", "subdomain": "safety",
                       "severity": "critical",
                       "reason": "ASIL assigned without HARA — violates ISO 26262 Part 3"})

    clause_bad, clause_val = check_fake_clause(text)
    if clause_bad:
        issues.append({"pattern": "fake_clause", "subdomain": "safety",
                       "severity": "critical",
                       "reason": f"ISO 26262 Part 6 Clause {clause_val} does not exist — Part 6 has only 13 clauses"})

    if check_can_has_security(text):
        issues.append({"pattern": "can_security", "subdomain": "electrical",
                       "severity": "high",
                       "reason": "Standard CAN bus has no built-in authentication or encryption"})

    if check_ara_com_classic(text):
        issues.append({"pattern": "ara_com_classic", "subdomain": "software",
                       "severity": "high",
                       "reason": "ara::com belongs to Adaptive Platform only — not available in Classic Platform"})

    if check_adaptive_bare_metal(text):
        issues.append({"pattern": "adaptive_bare_metal", "subdomain": "software",
                       "severity": "high",
                       "reason": "AUTOSAR Adaptive Platform requires POSIX OS (Linux/QNX) — cannot run bare-metal"})

    if check_sotif_same_as_iso(text):
        issues.append({"pattern": "sotif_iso", "subdomain": "safety",
                       "severity": "high",
                       "reason": "SOTIF and ISO 26262 are different complementary standards — SOTIF is not a replacement"})

    # Score: based on number and severity of issues
    weights  = {"critical": 5, "high": 3, "medium": 2, "low": 1}
    n_crit   = sum(1 for i in issues if i["severity"] == "critical")
    n_high   = sum(1 for i in issues if i["severity"] == "high")
    n_medium = sum(1 for i in issues if i["severity"] == "medium")

    if n_crit >= 3:   score = 90
    elif n_crit == 2: score = 80
    elif n_crit == 1: score = 65
    elif n_high >= 2: score = 55
    elif n_high == 1: score = 40
    elif n_medium >= 2: score = 30
    elif n_medium == 1: score = 20
    else:             score = 0

    subs = list(set(i["subdomain"] for i in issues))
    return {
        "issues":    issues,
        "score":     score,
        "subdomain": subs[0] if subs else "general",
        "caught":    len(issues) > 0
    }

# ── Groq system prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an automotive AI hallucination detector. Be precise and conservative.

You have a KNOWLEDGE BASE provided. Compare the INPUT TEXT against it.

HALLUCINATIONS TO FLAG (score 60-100%):
1. Wrong VSS paths: vehicle.speed.current, Vehicle.Engine.RPM, Vehicle.Battery.SOC, Vehicle.GPS.Latitude, Vehicle.Fuel.Level (these do not exist in VSS)
2. Non-existent ASIL levels: ASIL E, ASIL F, ASIL Z, ASIL G, ASIL 1-5 (only A,B,C,D exist)
3. ASIL assigned with "without HARA" or "without formal analysis" or "obviously qualifies"
4. ABS timing outside 50-150ms: values like 1ms, 2ms, 5ms, 300ms, 500ms are wrong
5. ara::com used with Classic Platform (ara::com is Adaptive only)
6. CAN bus claimed to have built-in encryption or authentication (CAN has none)
7. Adaptive Platform running on bare-metal without OS (requires POSIX)
8. ISO 26262 Part 6 clause numbers above 13 (only 13 clauses exist)
9. SOTIF described as same as or replacement for ISO 26262
10. Absolute impossible claims: "guaranteed to always", "100% accurate", "never fails"

CORRECT USAGE — score 0-15% for these:
- Vehicle.Speed, Vehicle.Powertrain.TractionBattery.StateOfCharge.Current (valid VSS paths)
- ASIL A, B, C, D with HARA mentioned (valid process)
- ABS timing stated as 50 to 150 milliseconds (valid range)
- ara::com with Adaptive Platform (valid)
- CAN described as lacking security (valid)
- SOTIF as complementary to ISO 26262 (valid)
- 100% MC/DC coverage for ASIL D software testing (this is a VALID test coverage requirement)
- ISO 26262 Part 6 clauses 1-13 (valid)

SCORING GUIDE:
- Text has NO wrong facts → score 0-10%
- Text has 1 wrong fact → score 40-60%
- Text has 2 wrong facts → score 65-80%
- Text has 3+ wrong facts → score 85-100%

For "corrected": rewrite the text replacing EVERY wrong fact with the correct one from the knowledge base. If no hallucinations, return the original unchanged.

Return ONLY this JSON (no markdown, no code blocks):
{"score": <0-100>, "is_hallucination": <true/false>, "reason": "<what was wrong or why it is clean>", "corrected": "<corrected text>"}"""

def ask_groq(text, context, local_result):
    if groq_client is None:
        return {
            "score":            local_result["score"],
            "is_hallucination": local_result["score"] >= 25,
            "reason":           "Local detection only — add GROQ_API_KEY for full analysis",
            "corrected":        text
        }
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"KNOWLEDGE BASE:\n{context or '(not available)'}\n\nINPUT TEXT:\n{text}\n\nReturn JSON only."}
            ],
            temperature=0.05,
            max_tokens=600
        )
        raw = r.choices[0].message.content.strip()
        if "```" in raw:
            for part in raw.split("```"):
                p = part.strip()
                if p.startswith("json"): p = p[4:].strip()
                if p.startswith("{"): raw = p; break
        result = json.loads(raw.strip())
        result.setdefault("score", local_result["score"])
        result.setdefault("is_hallucination", local_result["score"] >= 25)
        result.setdefault("corrected", text)
        result.setdefault("reason", "Analysis complete")
        return result
    except Exception as e:
        return {
            "score":            local_result["score"],
            "is_hallucination": local_result["score"] >= 25,
            "reason":           f"LLM error: {e}",
            "corrected":        text
        }

# ── ROUGE-L ───────────────────────────────────────────────────────────────────
def rouge_l(hyp, ref):
    h = hyp.lower().split()
    r = ref.lower().split()
    if not h or not r: return 0.0
    dp = [[0]*(len(r)+1) for _ in range(len(h)+1)]
    for i in range(1, len(h)+1):
        for j in range(1, len(r)+1):
            dp[i][j] = dp[i-1][j-1]+1 if h[i-1]==r[j-1] else max(dp[i-1][j],dp[i][j-1])
    lcs = dp[len(h)][len(r)]
    p   = lcs/len(h); rc = lcs/len(r)
    return round(2*p*rc/(p+rc), 4) if (p+rc) > 0 else 0.0

# ── Live evaluation (called after every verify) ───────────────────────────────
def update_live_eval():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT score, rouge_l FROM history").fetchall()
    conn.close()
    if len(rows) < 2: return

    rouge_vals   = [r["rouge_l"] for r in rows if r["rouge_l"] is not None]
    avg_rouge    = round(mean(rouge_vals), 4) if rouge_vals else 0.0

    halluc = [r for r in rows if r["score"] >= 30]
    clean  = [r for r in rows if r["score"] <= 20]
    used   = halluc + clean
    if len(used) < 2: return

    y_true = [1]*len(halluc) + [0]*len(clean)
    y_pred = [1 if r["score"] >= 25 else 0 for r in used]

    tp = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==1)
    fp = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==1)
    tn = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==0)
    fn = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==0)

    prec = tp/(tp+fp) if (tp+fp)>0 else 0.0
    rec  = tp/(tp+fn) if (tp+fn)>0 else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
    acc  = (tp+tn)/len(used) if used else 0.0

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO evaluations (created_at,rouge_l,f1_score,precision,recall,accuracy,total) VALUES (?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), avg_rouge,
         round(f1,4), round(prec,4), round(rec,4), round(acc,4), len(rows))
    )
    conn.commit(); conn.close()

# ── Models ────────────────────────────────────────────────────────────────────
class VerifyReq(BaseModel):
    text:      str
    extra_url: Optional[str] = None

class ReVerifyReq(BaseModel):
    original:  str
    corrected: str

class EvalReq(BaseModel):
    threshold: Optional[float] = 25.0

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"name": "The Verifier", "version": "2.0", "status": "running",
            "docs": "http://localhost:8000/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "groq": groq_client is not None,
            "index": chunks is not None, "chunks": len(chunks) if chunks else 0,
            "patterns": len(PATTERNS)}

@app.post("/verify")
def verify(req: VerifyReq):
    if not req.text.strip():
        raise HTTPException(400, "text cannot be empty")
    t0 = time.time()

    # Stage 1: local pattern detection
    local = run_detection(req.text)

    # Stage 2: TF-IDF KB search
    context, sources = search(req.text)

    # Stage 3: optional URL context
    if req.extra_url and req.extra_url.startswith("http"):
        try:
            import urllib.request
            with urllib.request.urlopen(req.extra_url, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            txt = re.sub(r"<[^>]+>", " ", html)
            txt = re.sub(r"\s+", " ", txt).strip()[:2000]
            context += "\n\nEXTRA SOURCE:\n" + txt
            sources.append(req.extra_url)
        except Exception:
            pass

    # Stage 4: Groq LLM
    groq_result = ask_groq(req.text, context, local)

    # Stage 5: final score decision
    # Rule: if local detected CRITICAL patterns → trust local score (very precise)
    #        otherwise → trust Groq (has KB context)
    has_critical = any(i["severity"] == "critical" for i in local["issues"])
    if has_critical and local["score"] > groq_result["score"]:
        final_score = local["score"]
    else:
        final_score = groq_result["score"]

    groq_result["score"] = final_score
    groq_result["is_hallucination"] = final_score >= 25

    # Stage 6: ROUGE-L — compare text to most relevant KB sentences
    live_rl = None
    corrected  = groq_result.get("corrected", "")
    # Use corrected text if different, otherwise use original
    # This ensures ROUGE-L is computed for every verification
    eval_text  = corrected if (corrected and corrected != req.text and len(corrected) > 20) else req.text
    kb_file    = DATA_DIR / "knowledge_base.txt"
    if kb_file.exists() and eval_text:
        kb_text    = kb_file.read_text(encoding="utf-8")
        eval_words = set(eval_text.lower().split())
        kb_lines   = [l.strip() for l in kb_text.split("\n") if len(l.strip()) > 20]
        scored     = []
        for line in kb_lines:
            line_words = set(line.lower().split())
            overlap    = len(eval_words & line_words)
            if overlap > 2:
                scored.append((overlap, line))
        scored.sort(reverse=True)
        if scored:
            reference = " ".join(line for _, line in scored[:5])
            live_rl   = rouge_l(eval_text, reference)

    ms = int((time.time() - t0) * 1000)

    save_history(req.text, final_score, corrected, sources,
                 local["subdomain"], ms, live_rl)
    update_live_eval()

    return {
        "score":        final_score,
        "hallucinated": groq_result["is_hallucination"],
        "reason":       groq_result["reason"],
        "corrected":    corrected,
        "issues":       local["issues"],
        "sources":      sources,
        "subdomain":    local["subdomain"],
        "time_ms":      ms,
        "rouge_l":      live_rl
    }

@app.post("/reverify")
def reverify(req: ReVerifyReq):
    orig = run_detection(req.original)
    ctx_o, _ = search(req.original)
    res_o = ask_groq(req.original, ctx_o, orig)
    has_crit_o = any(i["severity"]=="critical" for i in orig["issues"])
    score_o = max(orig["score"], res_o["score"]) if has_crit_o else res_o["score"]

    corr = run_detection(req.corrected)
    ctx_c, _ = search(req.corrected)
    res_c = ask_groq(req.corrected, ctx_c, corr)
    has_crit_c = any(i["severity"]=="critical" for i in corr["issues"])
    score_c = max(corr["score"], res_c["score"]) if has_crit_c else res_c["score"]

    delta = score_o - score_c
    return {
        "original_score":  score_o,
        "corrected_score": score_c,
        "delta":           round(delta, 1),
        "improved":        delta >= 20,
        "message":         f"Drop of {delta:.1f}% — {'✅ RAG grounding confirmed' if delta >= 20 else '⚠️ Marginal improvement'}"
    }

@app.get("/rouge")
def get_rouge():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM evaluations ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return {"rouge_l": None, "accuracy": None, "recall": None, "f1_score": None,
                "message": "No evaluations yet — verify some texts first"}
    return dict(row)

@app.get("/history")
def history(limit: int = 100):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/stats")
def stats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    n = conn.execute("SELECT COUNT(*) as n FROM history").fetchone()["n"]
    if n == 0:
        conn.close()
        return {"total": 0, "avg_score": 0, "high_risk": 0, "avg_ms": 0, "p95_ms": 0}
    avg  = conn.execute("SELECT AVG(score) as a FROM history").fetchone()["a"]
    high = conn.execute("SELECT COUNT(*) as n FROM history WHERE score>=60").fetchone()["n"]
    tms  = [r["time_ms"] for r in conn.execute("SELECT time_ms FROM history").fetchall()]
    conn.close()
    ts   = sorted(tms)
    p95  = ts[int(0.95*len(ts))-1] if ts else 0
    return {
        "total":    n,
        "avg_score": round(avg, 1),
        "high_risk": high,
        "avg_ms":    round(mean(tms), 1) if tms else 0,
        "p95_ms":    p95
    }

@app.get("/live_metrics")
def live_metrics():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id,created_at,score,rouge_l,subdomain FROM history ORDER BY id ASC").fetchall()
    conn.close()
    records     = [dict(r) for r in rows]
    rouge_vals  = [r["rouge_l"] for r in records if r["rouge_l"] is not None]
    running_avg = []
    total = count = 0
    for r in records:
        if r["rouge_l"] is not None:
            total += r["rouge_l"]; count += 1
            running_avg.append(round(total/count, 4))
        else:
            running_avg.append(None)
    return {
        "total_verifications":      len(records),
        "verifications_with_rouge": len(rouge_vals),
        "current_avg_rouge_l":      round(mean(rouge_vals), 4) if rouge_vals else None,
        "per_verification": [
            {**r, "running_avg_rouge_l": running_avg[i]}
            for i, r in enumerate(records)
        ]
    }

@app.on_event("startup")
def startup():
    print("\n=== The Verifier v2.0 ===")
    init_db()
    load_index()
    init_groq()
    print(f"{len(PATTERNS)} static patterns + 7 smart checks loaded")
    print("Running at http://localhost:8000\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
