"""
The Verifier — Dashboard
Run: streamlit run dashboard.py
"""
import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
from pathlib import Path

API = "http://localhost:8000"
BASE_DIR = Path(__file__).parent

st.set_page_config(page_title="The Verifier", page_icon="🛡️", layout="wide")

# ── Global styling ────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 20% -10%, #12203f 0%, #0a0f1a 55%) fixed}
[data-testid="stSidebar"]{
  background: linear-gradient(180deg,#0f172a 0%,#0b1222 100%);
  border-right:1px solid #1e293b}
[data-testid="stSidebar"] .stButton>button{
  background:linear-gradient(90deg,#2563eb,#4f46e5); color:#fff; border:0;
  border-radius:8px; font-weight:600; transition:all .2s}
[data-testid="stSidebar"] .stButton>button:hover{
  filter:brightness(1.15); transform:translateY(-1px)}
[data-testid="stMetric"]{
  background:linear-gradient(180deg,#16233d 0%,#111a2e 100%);
  border:1px solid #24344f; border-radius:12px; padding:14px 16px;
  box-shadow:0 2px 10px rgba(0,0,0,.25)}
[data-testid="stMetric"] label{color:#7c8db0 !important; font-size:11px !important;
  text-transform:uppercase; letter-spacing:.06em}
[data-testid="stMetricValue"]{color:#e2e8f0 !important}
.stTabs [data-baseweb="tab-list"]{gap:6px; border-bottom:1px solid #1e293b}
.stTabs [data-baseweb="tab"]{
  background:#111a2e; border-radius:10px 10px 0 0; padding:8px 20px;
  color:#94a3b8; border:1px solid #1e293b; border-bottom:none}
.stTabs [aria-selected="true"]{
  background:linear-gradient(180deg,#1d2b4a,#16233d); color:#e2e8f0 !important;
  border-color:#2e4160}
div[data-testid="stExpander"]{
  background:#111a2e; border:1px solid #24344f; border-radius:12px}
div[data-testid="stExpander"] summary{color:#c7d2fe; font-weight:600}
h1,h2,h3{color:#e2e8f0}
hr{border-color:#1e293b}
.section-title{
  display:flex; align-items:center; gap:10px; margin:6px 0 10px 0;
  font-size:17px; font-weight:700; color:#e2e8f0}
.section-title .bar{width:5px; height:20px; border-radius:3px;
  background:linear-gradient(180deg,#6366f1,#2563eb)}
.hero{
  background:linear-gradient(90deg,#101c36 0%,#131b31 60%,#0f172a 100%);
  border:1px solid #24344f; border-radius:16px; padding:18px 24px; margin-bottom:14px;
  display:flex; align-items:center; justify-content:space-between}
.hero .t{font-size:26px; font-weight:800; color:#e2e8f0}
.hero .s{font-size:13px; color:#7c8db0; margin-top:2px}
.hero .pill{
  font-size:11px; font-weight:700; padding:6px 14px; border-radius:999px;
  border:1px solid; letter-spacing:.04em}
</style>""", unsafe_allow_html=True)

def get(url):
    try: return requests.get(url, timeout=4).json(), True
    except: return {}, False

def post(url, data, timeout=30):
    try: return requests.post(url, json=data, timeout=timeout).json(), True
    except Exception as e: return {"error": str(e)}, False

def section(title):
    st.markdown(f'<div class="section-title"><div class="bar"></div>{title}</div>',
                unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ The Verifier")
    st.markdown("**Automotive AI Hallucination Detection**")
    st.markdown("---")

    h, ok = get(f"{API}/health")
    if ok: st.success(f"✅ Online | Groq: {'✓' if h.get('groq') else '✗'} | Chunks: {h.get('chunks',0)}")
    else:  st.error("❌ Offline — run: python server.py")

    st.markdown("---")
    st.markdown("#### Verify Text")
    text = st.text_area("Paste LLM text:", height=120,
                         placeholder="Paste automotive LLM output here...")
    url  = st.text_input("Extra URL (optional):")

    c1, c2 = st.columns(2)
    with c1: verify_btn   = st.button("🔍 Verify",    use_container_width=True)
    with c2: reverify_btn = st.button("🔄 Re-verify", use_container_width=True)

    if verify_btn:
        if not text.strip(): st.warning("Enter text first")
        else:
            with st.spinner("Analyzing..."):
                payload = {"text": text}
                if url.strip(): payload["extra_url"] = url.strip()
                res, ok = post(f"{API}/verify", payload, timeout=30)
            if not ok: st.error(f"Error: {res.get('error')}")
            else:
                sc = res.get("score", 0)
                if   sc >= 60: st.error(f"🚨 {sc}% — High risk")
                elif sc >= 40: st.warning(f"⚠️ {sc}% — Medium risk")
                elif sc >= 20: st.info(f"🔶 {sc}% — Low risk")
                else:          st.success(f"✅ {sc}% — Clean")
                for iss in res.get("issues", [])[:4]:
                    sev  = iss.get("severity","")
                    icon = "🔴" if sev=="critical" else "🟠" if sev=="high" else "🟡"
                    st.markdown(f"<small>{icon} {iss.get('reason','')}</small>",
                                unsafe_allow_html=True)
                if res.get("corrected") and res["corrected"] != text:
                    with st.expander("✅ Corrected version"):
                        st.write(res["corrected"])
                if res.get("rouge_l") is not None:
                    st.caption(f"📐 ROUGE-L this text: {res['rouge_l']:.3f}")
                if res.get("sources"):
                    st.caption("📚 " + ", ".join(res["sources"]))
                st.session_state["orig"] = text
                st.session_state["corr"] = res.get("corrected","")

    if reverify_btn:
        orig = st.session_state.get("orig","")
        corr = st.session_state.get("corr","")
        if not orig: st.warning("Run Verify first")
        else:
            with st.spinner("Re-verifying..."):
                res, ok = post(f"{API}/reverify",
                               {"original": orig, "corrected": corr}, timeout=60)
            if ok:
                if res.get("improved"):
                    st.success(f"✅ {res.get('message')}\n\n"
                               f"Before: {res['original_score']}% → After: {res['corrected_score']}%")
                else:
                    st.info(f"{res.get('message')}")

    st.markdown("---")
    st.caption("📚 KB: COVESA VSS · ISO 26262 · SOTIF · CAN Bus · AUTOSAR")
    st.caption("🤖 Groq gpt-oss-120b | 🔍 TF-IDF Search")

# ── MAIN PAGE ─────────────────────────────────────────────────────────────────
h_ok = ok and h.get("groq")
pill = ('<span class="pill" style="color:#34d399;border-color:#34d39955;background:#34d39912">● LIVE — FULL PIPELINE</span>'
        if h_ok else
        '<span class="pill" style="color:#fbbf24;border-color:#fbbf2455;background:#fbbf2412">● LOCAL DETECTION ONLY</span>'
        if ok else
        '<span class="pill" style="color:#f87171;border-color:#f8717155;background:#f8717112">● BACKEND OFFLINE</span>')
st.markdown(f"""
<div class="hero">
  <div>
    <div class="t">🛡️ The Verifier</div>
    <div class="s">Automotive AI Hallucination Detection — Hybrid RAG · Groq gpt-oss-120b · TF-IDF</div>
  </div>
  {pill}
</div>""", unsafe_allow_html=True)

stats, ok_s   = get(f"{API}/stats")
rouge_d, _    = get(f"{API}/rouge")
history, ok_h = get(f"{API}/history")

rouge_val = rouge_d.get("rouge_l")
acc_val   = rouge_d.get("accuracy")
rec_val   = rouge_d.get("recall")

def badge(label, value, color, note):
    return f"""<div style="background:linear-gradient(180deg,#16233d 0%,#111a2e 100%);
     border:1px solid #24344f; border-top:3px solid {color};
     border-radius:12px;padding:14px 8px;text-align:center;
     box-shadow:0 2px 10px rgba(0,0,0,.25)">
  <div style="font-size:10px;color:#7c8db0;font-weight:700;text-transform:uppercase;
       letter-spacing:.06em;margin-bottom:4px">{label}</div>
  <div style="font-size:24px;font-weight:700;color:{color};line-height:1.1">{value}</div>
  <div style="font-size:9px;color:#475569;margin-top:2px">{note}</div>
</div>"""

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
with c1: st.markdown(badge("Verifications", stats.get("total",0), "#e2e8f0", "total runs"), unsafe_allow_html=True)
with c2: st.markdown(badge("Avg Halluc %", f"{stats.get('avg_score',0)}%", "#f59e0b", "all history"), unsafe_allow_html=True)
with c3: st.markdown(badge("High Risk", stats.get("high_risk",0), "#ef4444", "score ≥ 60%"), unsafe_allow_html=True)
with c4: st.markdown(badge("Avg Speed", f"{stats.get('avg_ms',0):.0f} ms", "#38bdf8", "full pipeline"), unsafe_allow_html=True)
with c5:
    if rouge_val is not None:
        c = "#10b981" if rouge_val>=0.4 else "#f97316" if rouge_val>=0.2 else "#64748b"
        st.markdown(badge("ROUGE-L", f"{rouge_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge("ROUGE-L", "—", "#475569", "verify first"), unsafe_allow_html=True)
with c6:
    if acc_val is not None:
        c = "#3b82f6" if acc_val>=0.8 else "#f97316" if acc_val>=0.6 else "#ef4444"
        st.markdown(badge("Accuracy", f"{acc_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Accuracy", "—", "#475569", "verify first"), unsafe_allow_html=True)
with c7:
    if rec_val is not None:
        c = "#6366f1" if rec_val>=0.8 else "#f97316" if rec_val>=0.6 else "#ef4444"
        st.markdown(badge("Recall", f"{rec_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Recall", "—", "#475569", "verify first"), unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Statistics", "📋 History", "🏆 Paper Benchmark (n=300)"])

with tab1:
    if not ok_s: st.error("Cannot reach backend.")
    elif not history: st.info("No verifications yet — use sidebar.")
    else:
        clean  = sum(1 for r in history if r.get("score",0) <  25)
        low    = sum(1 for r in history if 25 <= r.get("score",0) < 40)
        medium = sum(1 for r in history if 40 <= r.get("score",0) < 60)
        high   = sum(1 for r in history if r.get("score",0) >= 60)
        rc1,rc2,rc3,rc4 = st.columns(4)
        with rc1: st.markdown(badge("✅ Clean", clean, "#10b981", "0–24%"), unsafe_allow_html=True)
        with rc2: st.markdown(badge("🔶 Low", low, "#eab308", "25–39%"), unsafe_allow_html=True)
        with rc3: st.markdown(badge("⚠️ Medium", medium, "#f97316", "40–59%"), unsafe_allow_html=True)
        with rc4: st.markdown(badge("🚨 High", high, "#ef4444", "≥ 60%"), unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section("Hallucination Score per Verification")

        hist_all, _ = get(f"{API}/history?limit=5000")
        dfa = pd.DataFrame(hist_all).sort_values("id").reset_index(drop=True)
        dfa["subdomain"] = dfa["subdomain"].fillna("general")

        with st.expander("🎛️ Filters", expanded=False):
            fc1, fc2, fc3 = st.columns([2, 2, 2])
            with fc1:
                show_n = st.select_slider("Last N verifications",
                          options=[25, 50, 100, 250, 500, "All"], value=50)
            with fc2:
                dom_opts = sorted(dfa["subdomain"].unique().tolist())
                dom_sel  = st.multiselect("Domain", dom_opts, default=dom_opts)
            with fc3:
                risk_sel = st.multiselect("Risk level",
                            ["Clean (0-39%)", "Borderline (40-49%)", "Flagged (>=50%)"],
                            default=["Clean (0-39%)", "Borderline (40-49%)", "Flagged (>=50%)"])

        dfa = dfa[dfa["subdomain"].isin(dom_sel)]
        def risk_band(s):
            return "Flagged (>=50%)" if s >= 50 else "Borderline (40-49%)" if s >= 40 else "Clean (0-39%)"
        dfa["Risk band"] = dfa["score"].apply(risk_band)
        dfa = dfa[dfa["Risk band"].isin(risk_sel)]
        if show_n != "All":
            dfa = dfa.tail(int(show_n))

        if dfa.empty:
            st.info("No verifications match the selected filters.")
        else:
            base = alt.Chart(dfa).encode(
                x=alt.X("id:Q", title="Verification ID",
                        scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
                y=alt.Y("score:Q", title="Hallucination score (%)",
                        scale=alt.Scale(domain=[0, 100])),
                tooltip=[alt.Tooltip("id:Q", title="ID"),
                         alt.Tooltip("score:Q", title="Score %"),
                         alt.Tooltip("subdomain:N", title="Domain"),
                         alt.Tooltip("input_text:N", title="Input")])
            points = base.mark_circle(size=70, opacity=0.9).encode(
                color=alt.Color("Risk band:N",
                    scale=alt.Scale(
                        domain=["Clean (0-39%)", "Borderline (40-49%)", "Flagged (>=50%)"],
                        range=["#10b981", "#f97316", "#ef4444"]),
                    legend=alt.Legend(orient="bottom", title=None)))
            line = base.mark_line(color="#64748b", opacity=0.3)
            warn_rule   = alt.Chart(pd.DataFrame({"y": [50]})).mark_rule(
                color="#ef4444", strokeDash=[6, 4]).encode(y="y:Q")
            border_rule = alt.Chart(pd.DataFrame({"y": [40]})).mark_rule(
                color="#f97316", strokeDash=[6, 4]).encode(y="y:Q")
            st.altair_chart((line + points + warn_rule + border_rule)
                            .properties(height=300), use_container_width=True)
            st.caption(f"Showing {len(dfa)} of {len(hist_all)} verifications · hover a point for details")

with tab2:
    h2, ok2 = get(f"{API}/history?limit=200")
    if not ok2 or not h2: st.info("No history yet.")
    else:
        rows = []
        for r in h2:
            sc     = r.get("score",0)
            answer = r.get("corrected") or ""
            rows.append({
                "ID":      r.get("id"),
                "Time":    r.get("created_at","")[:19].replace("T"," "),
                "Input (prompt tested)": r.get("input_text","")[:70]+("..." if len(r.get("input_text",""))>70 else ""),
                "Model answer (corrected)": answer[:70]+("..." if len(answer)>70 else "") if answer else "—",
                "Score %": sc,
                "Risk":    "🚨 High" if sc>=60 else "⚠️ Med" if sc>=40 else "🔶 Low" if sc>=20 else "✅ Clean",
                "Domain":  (r.get("subdomain") or "general").capitalize(),
                "ROUGE-L": f"{r['rouge_l']:.3f}" if r.get("rouge_l") is not None else "—",
                "ms":      r.get("time_ms",0)
            })
        df = pd.DataFrame(rows)
        srch = st.text_input("Search:", placeholder="Filter text...")
        if srch: df = df[df["Input (prompt tested)"].str.contains(srch, case=False, na=False)]
        st.dataframe(df, hide_index=True, use_container_width=True,
            column_config={"Score %": st.column_config.ProgressColumn(
                "Score %", min_value=0, max_value=100, format="%d%%")})

        section("🔎 Inspect a verification by ID")
        by_id  = {r["id"]: r for r in h2}
        sel_id = st.selectbox("Choose an ID:", options=list(by_id.keys()),
                              format_func=lambda i: f"#{i} — {by_id[i].get('input_text','')[:50]}")
        sel = by_id[sel_id]
        a, b = st.columns(2)
        with a:
            st.markdown(f"**Input (ID #{sel_id}):**")
            st.code(sel.get("input_text",""), language="text")
        with b:
            st.markdown("**Model answer (corrected version):**")
            st.code(sel.get("corrected") or "(no correction — text was clean)", language="text")
        st.write(f"Score: **{sel.get('score',0)}%** | Domain: {sel.get('subdomain','—')} | "
                 f"ROUGE-L: {sel.get('rouge_l') if sel.get('rouge_l') is not None else '—'} | "
                 f"Time: {sel.get('time_ms',0)}ms | Date: {sel.get('created_at','')[:19].replace('T',' ')}")

with tab3:
    st.caption("This is the formal, fixed 300-case evaluation from `evaluation/run_evaluation.py` — "
               "a separate, controlled measurement from the live demo stats above. These are the "
               "numbers reported in the paper's Table I.")
    eval_path = BASE_DIR / "evaluation" / "evaluation_results.json"
    if not eval_path.exists():
        st.warning("No evaluation_results.json found yet. Run:\n\n"
                   "cd evaluation && python run_evaluation.py --mode full")
    else:
        eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
        run = eval_data[0] if isinstance(eval_data, list) else eval_data

        section(f"{run.get('name','Full pipeline')} — n = {run.get('n','—')}")
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1: st.markdown(badge("Accuracy", f"{run.get('accuracy',0):.3f}", "#3b82f6", "n=300"), unsafe_allow_html=True)
        with ec2: st.markdown(badge("Precision", f"{run.get('precision',0):.3f}", "#10b981", "n=300"), unsafe_allow_html=True)
        with ec3: st.markdown(badge("Recall", f"{run.get('recall',0):.3f}", "#6366f1", "n=300"), unsafe_allow_html=True)
        with ec4: st.markdown(badge("F1", f"{run.get('f1',0):.3f}", "#f59e0b", "n=300"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section("Confusion Matrix")
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1: st.markdown(badge("True Positive", run.get("tp","—"), "#10b981", "caught hallucinations"), unsafe_allow_html=True)
        with cm2: st.markdown(badge("False Positive", run.get("fp","—"), "#f97316", "false alarms"), unsafe_allow_html=True)
        with cm3: st.markdown(badge("True Negative", run.get("tn","—"), "#10b981", "correctly passed"), unsafe_allow_html=True)
        with cm4: st.markdown(badge("False Negative", run.get("fn","—"), "#ef4444", "missed"), unsafe_allow_html=True)

        ci = run.get("acc_ci")
        if ci:
            st.caption(f"95% CI on accuracy: {ci[0]:.3f} – {ci[1]:.3f}")

        # optional per-subdomain breakdown, if present in the saved results
        subs = run.get("per_subdomain") or run.get("subdomains")
        if subs:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            section("Per Subdomain")
            st.dataframe(pd.DataFrame(subs), hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("ROUGE-L — Ji et al. (2022) · Precision/Recall/F1 — Mahawatta Dona et al. (2024)")
