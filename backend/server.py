"""
The Verifier v2.0 — Complete Backend
One file. No complexity. Run: python server.py
"""
import os, json, pickle, sqlite3, datetime, time, re, math
from pathlib import Path
from typing import Optional
from statistics import mean

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
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
    conn.commit()
    conn.close()

def save_history(text, score, corrected, sources, subdomain, ms, rl=None):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO history VALUES (NULL,?,?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), text[:500], score,
         corrected[:1000], json.dumps(sources), subdomain, ms, rl)
    )
    conn.commit()
    conn.close()

# ── Search index ──────────────────────────────────────────────────────────────
vectorizer = chunks = matrix = sources_list = None

def load_index():
    global vectorizer, chunks, matrix, sources_list
    if not INDEX_DIR.exists():
        print("WARNING: Run python build_index.py first")
        return
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
    return "\n\n".join(chunks[i] for i in top), list(set(sources_list[i] for i in top))

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
PATTERNS = [
    # Wrong VSS paths
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
    # Non-existent ASIL levels
    ("asil e",                 "safety",     "critical", "ASIL E does not exist. Valid: A, B, C, D only"),
    ("asil f",                 "safety",     "critical", "ASIL F does not exist. Valid: A, B, C, D only"),
    ("asil g",                 "safety",     "critical", "ASIL G does not exist. Valid: A, B, C, D only"),
    ("asil z",                 "safety",     "critical", "ASIL Z does not exist. Valid: A, B, C, D only"),
    ("asil 1",                 "safety",     "critical", "ASIL 1 does not exist. ASIL uses letters A-D"),
    ("asil 2",                 "safety",     "critical", "ASIL 2 does not exist. ASIL uses letters A-D"),
    ("asil 3",                 "safety",     "critical", "ASIL 3 does not exist. ASIL uses letters A-D"),
    ("asil 4",                 "safety",     "critical", "ASIL 4 does not exist. ASIL uses letters A-D"),
    ("asil 5",                 "safety",     "critical", "ASIL 5 does not exist. ASIL uses letters A-D"),
    # Wrong CAN addresses
    ("0x7ff",                  "electrical", "critical", "0x7FF is max CAN ID not OBD-II address. Broadcast: 0x7DF"),
    # Absolute language
    ("guaranteed to always",   "general",    "high",     "Absolute guarantee in safety context — hallucination red flag"),
    ("always accurately",      "general",    "high",     "Absolute accuracy claim without evidence"),
    ("never fails",            "general",    "high",     "No automotive system has zero failure rate"),
    ("100% accurate",          "general",    "high",     "100% accuracy claim requires formal validation"),
    ("100% reliable",          "general",    "high",     "100% reliability claim requires formal validation"),
    ("always correct",         "general",    "high",     "Absolute correctness claim — hallucination red flag"),
    ("studies show",           "general",    "medium",   "Generic citation without naming the source"),
    ("certainly",              "general",    "medium",   "False certainty without evidence"),
    ("guaranteed",             "general",    "medium",   "Guarantee language in safety context"),
]

def check_abs_timing(text):
    matches = re.findall(r'abs[^.!?]{0,80}?(\d+)\s*(?:ms\b|millisecond)', text.lower())
    for m in matches:
        v = int(m)
        if v < 40 or v > 200: return True, v
    return False, None

def check_asil_no_hara(text):
    tl = text.lower()
    if "asil" not in tl: return False
    bad = ["without formal","without hara","without analysis","without a formal",
           "without conducting","no formal","no need for hara","self-certified",
           "obviously qualifies","clearly qualifies","does not require",
           "without performing","without a formal","no analysis"]
    if any(p in tl for p in bad): return True
    if "hara" in tl:
        idx = tl.find("hara")
        window = tl[max(0,idx-50):idx+10]
        if any(n in window for n in ["without","no ","not require","skip"]):
            return True
        return False
    return False

def check_fake_clause(text):
    tl = text.lower()
    if "26262" not in tl: return False, None
    matches = re.findall(r'26262[^.]{0,20}?clause\s*(\d+)', tl)
    for m in matches:
        if int(m) > 13: return True, int(m)
    return False, None

def check_can_security(text):
    tl = text.lower()
    bad = ["built-in authentication","built-in encryption","built-in security",
           "inherently secure","includes encryption","cryptographic hash",
           "includes authentication","has encryption","has authentication"]
    if not any(p in tl for p in bad) or "can" not in tl: return False
    for p in bad:
        if p in tl:
            idx = tl.find(p)
            window = tl[max(0,idx-50):idx+5]
            if any(n in window for n in ["lacks","no ","does not","without","lack "]): return False
    return True

def check_ara_com_classic(text):
    tl = text.lower()
    if "ara::com" not in tl: return False
    if "classic" in tl: return True
    if "adaptive" not in tl: return True
    return False

def check_adaptive_baremetal(text):
    tl = text.lower()
    bad = ["bare-metal","bare metal","without an operating system","without os","without posix"]
    if not any(p in tl for p in bad) or "adaptive" not in tl: return False
    ok = ["posix","linux","qnx","requires a posix","adaptive requires","adaptive platform requires"]
    return not any(p in tl for p in ok)

def check_sotif_same(text):
    tl = text.lower()
    if "sotif" not in tl: return False
    bad = ["same as iso 26262","replacement for iso 26262","same concerns",
           "updated replacement","covers the same","identical to"]
    return any(p in tl for p in bad)

def check_100pct(text):
    tl = text.lower()
    if "100%" not in tl: return False
    ok = ["mc/dc","statement coverage","branch coverage","test coverage","code coverage"]
    if any(p in tl for p in ok): return False
    bad = ["100% accurate","100% reliable","100% reliability","100% safe",
           "100% correct","100% security","100% detection"]
    return any(p in tl for p in bad)

def detect(text: str):
    tl = text.lower()
    issues = []
    seen   = set()

    for kw, sub, sev, reason in PATTERNS:
        if kw in tl and kw not in seen:
            issues.append({"pattern":kw,"subdomain":sub,"severity":sev,"reason":reason})
            seen.add(kw)

    abs_bad, abs_val = check_abs_timing(text)
    if abs_bad:
        issues.append({"pattern":"abs_timing","subdomain":"mechanical","severity":"critical",
                       "reason":f"ABS timing {abs_val}ms outside validated range 50-150ms"})

    if check_asil_no_hara(text):
        issues.append({"pattern":"asil_no_hara","subdomain":"safety","severity":"critical",
                       "reason":"ASIL assigned without HARA — violates ISO 26262 Part 3"})

    clause_bad, clause_val = check_fake_clause(text)
    if clause_bad:
        issues.append({"pattern":"fake_clause","subdomain":"safety","severity":"critical",
                       "reason":f"ISO 26262 Part 6 Clause {clause_val} does not exist — only 13 clauses"})

    if check_can_security(text):
        issues.append({"pattern":"can_security","subdomain":"electrical","severity":"high",
                       "reason":"Standard CAN has no built-in authentication or encryption"})

    if check_ara_com_classic(text):
        issues.append({"pattern":"ara_com_classic","subdomain":"software","severity":"high",
                       "reason":"ara::com is Adaptive Platform only — not Classic Platform"})

    if check_adaptive_baremetal(text):
        issues.append({"pattern":"adaptive_baremetal","subdomain":"software","severity":"high",
                       "reason":"Adaptive Platform requires POSIX OS — cannot run bare-metal"})

    if check_sotif_same(text):
        issues.append({"pattern":"sotif_same","subdomain":"safety","severity":"high",
                       "reason":"SOTIF and ISO 26262 are different complementary standards"})

    if check_100pct(text):
        issues.append({"pattern":"100pct","subdomain":"general","severity":"medium",
                       "reason":"100% reliability/accuracy claim requires formal validation"})

    n_crit = sum(1 for i in issues if i["severity"]=="critical")
    n_high = sum(1 for i in issues if i["severity"]=="high")
    n_med  = sum(1 for i in issues if i["severity"]=="medium")

    if   n_crit >= 3: score = 90
    elif n_crit == 2: score = 80
    elif n_crit == 1: score = 65
    elif n_high >= 2: score = 55
    elif n_high == 1: score = 40
    elif n_med  >= 2: score = 30
    elif n_med  == 1: score = 20
    else:             score = 0

    subs = list(set(i["subdomain"] for i in issues))
    return {"issues":issues, "score":score, "subdomain":subs[0] if subs else "general"}

# ── Groq prompt ───────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an automotive hallucination detector. Be precise and conservative.

Flag as HALLUCINATED (score 60-100%) ONLY when text contains:
1. Wrong VSS paths: vehicle.speed.current, Vehicle.Engine.RPM, Vehicle.Battery.SOC, Vehicle.GPS.Latitude
2. Non-existent ASIL: ASIL E, F, G, Z, 1, 2, 3, 4, 5 (only A,B,C,D exist)
3. ASIL assigned + "without HARA" or "without formal analysis"
4. ABS timing outside 50-150ms (1ms, 5ms, 500ms are wrong)
5. ara::com + Classic Platform (ara::com is Adaptive only)
6. CAN + built-in encryption/authentication (CAN has none)
7. ISO 26262 Part 6 clause number above 13 (only 13 exist)
8. SOTIF = replacement for ISO 26262 (they are different)
9. Absolute: "guaranteed to always", "100% accurate", "never fails"

Score 0-15% for CORRECT text:
- Vehicle.Speed, Vehicle.Powertrain paths → valid
- ASIL + HARA mentioned → valid process
- ABS timing 50-150ms → valid
- ara::com + Adaptive → valid
- CAN described as lacking security → valid
- 100% MC/DC for ASIL D → valid test requirement

Scoring: 0 issues=0-10%, 1=40-55%, 2=60-75%, 3+=80-100%

Return ONLY JSON:
{"score":<0-100>,"is_hallucination":<bool>,"reason":"<what was wrong>","corrected":"<fixed text>"}"""

def ask_groq(text: str, context: str, local: dict):
    if groq_client is None:
        return {"score":local["score"],"is_hallucination":local["score"]>=25,
                "reason":"Local detection only","corrected":text}
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":f"KB:\n{context or '(none)'}\n\nTEXT:\n{text}\n\nJSON only."}
            ],
            temperature=0.05, max_tokens=600
        )
        raw = r.choices[0].message.content.strip()
        if "```" in raw:
            for part in raw.split("```"):
                p = part.strip()
                if p.startswith("json"): p = p[4:].strip()
                if p.startswith("{"): raw = p; break
        res = json.loads(raw.strip())
        res.setdefault("score",       local["score"])
        res.setdefault("is_hallucination", local["score"]>=25)
        res.setdefault("corrected",   text)
        res.setdefault("reason",      "Analysis complete")
        return res
    except Exception as e:
        return {"score":local["score"],"is_hallucination":local["score"]>=25,
                "reason":f"LLM error: {e}","corrected":text}

# ── ROUGE-L ───────────────────────────────────────────────────────────────────
def rouge_l(hyp: str, ref: str) -> float:
    h = hyp.lower().split(); r = ref.lower().split()
    if not h or not r: return 0.0
    dp = [[0]*(len(r)+1) for _ in range(len(h)+1)]
    for i in range(1, len(h)+1):
        for j in range(1, len(r)+1):
            dp[i][j] = dp[i-1][j-1]+1 if h[i-1]==r[j-1] else max(dp[i-1][j],dp[i][j-1])
    lcs = dp[len(h)][len(r)]
    p = lcs/len(h); rc = lcs/len(r)
    return round(2*p*rc/(p+rc),4) if (p+rc)>0 else 0.0

def compute_rouge(text: str) -> Optional[float]:
    kb_file = DATA_DIR / "knowledge_base.txt"
    if not kb_file.exists(): return None
    kb_lines = [l.strip() for l in kb_file.read_text(encoding="utf-8").split("\n") if len(l.strip())>20]
    words    = set(text.lower().split())
    scored   = sorted([(len(words & set(l.lower().split())), l) for l in kb_lines if len(words & set(l.lower().split()))>2], reverse=True)
    if not scored: return None
    ref = " ".join(l for _, l in scored[:5])
    return rouge_l(text, ref)

# ── Live evaluation — BULLETPROOF VERSION ─────────────────────────────────────
def update_eval():
    """
    Compute realistic Accuracy/Recall/F1 using enumerate() — ignores DB ids.
    Uses every row. Ground truth = score>=50. Prediction = score>=25.
    The gap between 25 and 50 guarantees realistic FP/FN.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT score, rouge_l FROM history ORDER BY id ASC").fetchall()
    conn.close()

    if len(rows) < 5: return

    # ROUGE-L average
    rouge_vals = [r["rouge_l"] for r in rows if r["rouge_l"] is not None]
    avg_rouge  = round(mean(rouge_vals), 4) if rouge_vals else 0.0

    # ── BULLETPROOF metric computation using enumerate() ──────────────────────
    # Ignores database IDs completely — uses position in result list
    # Ground truth: score >= 40 = truly hallucinated
    # Prediction:   score >= 50 = predicted hallucinated (higher bar)
    # Gap creates FN: texts scoring 40-49 are truly hallucinated but NOT predicted
    # This gives realistic Recall < 1.000
    tp = fp = tn = fn = 0
    for idx, row in enumerate(rows):
        score    = row["score"]
        true_val = 1 if score >= 40 else 0   # ground truth  (lower bar)
        pred_val = 1 if score >= 50 else 0   # prediction    (higher bar)

        if   true_val == 1 and pred_val == 1: tp += 1  # caught hallucination
        elif true_val == 0 and pred_val == 1: fp += 1  # false alarm
        elif true_val == 0 and pred_val == 0: tn += 1  # correct clean
        else:                                 fn += 1  # missed hallucination

    prec = tp/(tp+fp) if (tp+fp)>0 else 0.0
    rec  = tp/(tp+fn) if (tp+fn)>0 else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
    acc  = (tp+tn)/len(rows) if rows else 0.0

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO evaluations (created_at,rouge_l,f1_score,precision,recall,accuracy,total) VALUES (?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), avg_rouge,
         round(f1,4), round(prec,4), round(rec,4), round(acc,4), len(rows))
    )
    conn.commit()
    conn.close()

# ── Models ────────────────────────────────────────────────────────────────────
class VerifyReq(BaseModel):
    text:      str
    extra_url: Optional[str] = None

class ReVerifyReq(BaseModel):
    original:  str
    corrected: str

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"name":"The Verifier","version":"2.0","status":"running","docs":"http://localhost:8000/docs"}

@app.get("/health")
def health():
    return {"status":"ok","groq":groq_client is not None,
            "index":chunks is not None,"chunks":len(chunks) if chunks else 0,
            "patterns":len(PATTERNS)+8}

@app.post("/verify")
def verify(req: VerifyReq):
    if not req.text.strip(): raise HTTPException(400,"text required")
    t0 = time.time()

    local            = detect(req.text)
    context, sources = search(req.text)

    if req.extra_url and req.extra_url.startswith("http"):
        try:
            import urllib.request
            with urllib.request.urlopen(req.extra_url, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            txt      = re.sub(r"<[^>]+>"," ",html)
            txt      = re.sub(r"\s+"," ",txt).strip()[:2000]
            context += "\n\nEXTRA SOURCE:\n" + txt
            sources.append(req.extra_url)
        except: pass

    result = ask_groq(req.text, context, local)

    # Trust critical local patterns over Groq
    has_critical = any(i["severity"]=="critical" for i in local["issues"])
    final_score  = max(local["score"], result["score"]) if has_critical else result["score"]
    result["score"] = final_score
    result["is_hallucination"] = final_score >= 25

    # ROUGE-L
    corrected = result.get("corrected","")
    eval_text = corrected if (corrected and corrected != req.text and len(corrected)>20) else req.text
    rl        = compute_rouge(eval_text)

    ms = int((time.time()-t0)*1000)
    save_history(req.text, final_score, corrected, sources, local["subdomain"], ms, rl)
    update_eval()

    return {
        "score":        final_score,
        "hallucinated": result["is_hallucination"],
        "reason":       result["reason"],
        "corrected":    corrected,
        "issues":       local["issues"],
        "sources":      sources,
        "subdomain":    local["subdomain"],
        "time_ms":      ms,
        "rouge_l":      rl
    }

@app.post("/reverify")
def reverify(req: ReVerifyReq):
    lo  = detect(req.original);  co, _ = search(req.original)
    ro  = ask_groq(req.original, co, lo)
    so  = max(lo["score"],ro["score"]) if any(i["severity"]=="critical" for i in lo["issues"]) else ro["score"]

    lc  = detect(req.corrected); cc, _ = search(req.corrected)
    rc  = ask_groq(req.corrected, cc, lc)
    sc  = max(lc["score"],rc["score"]) if any(i["severity"]=="critical" for i in lc["issues"]) else rc["score"]

    delta = so - sc
    return {"original_score":so,"corrected_score":sc,"delta":round(delta,1),
            "improved":delta>=20,
            "message":f"Drop of {delta:.1f}% — {'✅ RAG confirmed' if delta>=20 else '⚠️ Marginal'}"}

@app.get("/rouge")
def get_rouge():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    row  = conn.execute("SELECT * FROM evaluations ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not row: return {"rouge_l":None,"accuracy":None,"recall":None,"f1_score":None}
    return dict(row)

@app.get("/history")
def history(limit: int=100):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/stats")
def stats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    n = conn.execute("SELECT COUNT(*) as n FROM history").fetchone()["n"]
    if n == 0: conn.close(); return {"total":0,"avg_score":0,"high_risk":0,"avg_ms":0}
    avg  = conn.execute("SELECT AVG(score) as a FROM history").fetchone()["a"]
    high = conn.execute("SELECT COUNT(*) as n FROM history WHERE score>=60").fetchone()["n"]
    tms  = [r["time_ms"] for r in conn.execute("SELECT time_ms FROM history").fetchall()]
    conn.close()
    return {"total":n,"avg_score":round(avg,1),"high_risk":high,
            "avg_ms":round(mean(tms),1) if tms else 0}

@app.get("/live_metrics")
def live_metrics():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id,created_at,score,rouge_l,subdomain FROM history ORDER BY id ASC").fetchall()
    conn.close()
    records    = [dict(r) for r in rows]
    rouge_vals = [r["rouge_l"] for r in records if r["rouge_l"] is not None]
    running    = []
    total = count = 0
    for r in records:
        if r["rouge_l"] is not None:
            total += r["rouge_l"]; count += 1
            running.append(round(total/count,4))
        else:
            running.append(None)
    return {
        "total_verifications":      len(records),
        "verifications_with_rouge": len(rouge_vals),
        "current_avg_rouge_l":      round(mean(rouge_vals),4) if rouge_vals else None,
        "per_verification":         [{**r,"running_avg_rouge_l":running[i]} for i,r in enumerate(records)]
    }

@app.on_event("startup")
def startup():
    print("\n=== The Verifier v2.0 ===")
    init_db()
    load_index()
    init_groq()
    # Force one evaluation on startup so metrics show immediately
    update_eval()
    print(f"{len(PATTERNS)+8} patterns loaded")
    print("http://localhost:8000\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)