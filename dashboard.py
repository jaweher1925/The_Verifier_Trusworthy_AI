"""
The Verifier — Dashboard
Run: streamlit run dashboard.py
"""
import streamlit as st
import requests
import pandas as pd

API = "http://localhost:8000"

st.set_page_config(page_title="The Verifier", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0a0f1a}
[data-testid="stSidebar"]{background:#0f172a}
div[data-testid="metric-container"]{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px}
</style>""", unsafe_allow_html=True)

def get(url):
    try: return requests.get(url, timeout=4).json(), True
    except: return {}, False

def post(url, data, timeout=30):
    try: return requests.post(url, json=data, timeout=timeout).json(), True
    except Exception as e: return {"error": str(e)}, False

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
                if res.get("rouge_l"):
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
                d = res.get("delta", 0)
                if res.get("improved"):
                    st.success(f"✅ {res.get('message')}\n\n"
                               f"Before: {res['original_score']}% → After: {res['corrected_score']}%")
                else:
                    st.info(f"{res.get('message')}")

    st.markdown("---")
    st.caption("📚 KB: COVESA VSS · ISO 26262 · SOTIF · CAN Bus · AUTOSAR")
    st.caption("🤖 Groq LLaMA 3.3 70B | 🔍 TF-IDF Search")

# ── MAIN PAGE ─────────────────────────────────────────────────────────────────
st.markdown("# 🛡️ The Verifier")
st.markdown("Automotive AI Hallucination Detection — RAG + Groq LLaMA 3.3 70B")
st.markdown("---")

stats, ok_s  = get(f"{API}/stats")
rouge_d, _   = get(f"{API}/rouge")
history, ok_h = get(f"{API}/history")

rouge_val = rouge_d.get("rouge_l")
acc_val   = rouge_d.get("accuracy")
rec_val   = rouge_d.get("recall")

def badge(label, value, color, note):
    return f"""<div style="background:#1e293b;border-top:3px solid {color};
     border-radius:10px;padding:14px 8px;text-align:center">
  <div style="font-size:10px;color:#64748b;font-weight:700;text-transform:uppercase;
       letter-spacing:.05em;margin-bottom:4px">{label}</div>
  <div style="font-size:24px;font-weight:700;color:{color};line-height:1.1">{value}</div>
  <div style="font-size:9px;color:#475569;margin-top:2px">{note}</div>
</div>"""

def badge_empty(label, note):
    return f"""<div style="background:#1e293b;border-top:3px solid #334155;
     border-radius:10px;padding:14px 8px;text-align:center">
  <div style="font-size:10px;color:#64748b;font-weight:700;text-transform:uppercase;
       letter-spacing:.05em;margin-bottom:4px">{label}</div>
  <div style="font-size:18px;font-weight:500;color:#475569;line-height:1.3">—</div>
  <div style="font-size:9px;color:#475569;margin-top:2px">{note}</div>
</div>"""

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
with c1: st.metric("Verifications",    stats.get("total",0))
with c2: st.metric("Avg Halluc %",     f"{stats.get('avg_score',0)}%")
with c3: st.metric("High Risk (≥60%)", stats.get("high_risk",0))
with c4: st.metric("Avg Speed",        f"{stats.get('avg_ms',0):.0f}ms")
with c5:
    if rouge_val is not None:
        c = "#10b981" if rouge_val>=0.4 else "#f97316" if rouge_val>=0.2 else "#64748b"
        st.markdown(badge("ROUGE-L", f"{rouge_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge_empty("ROUGE-L", "verify text first"), unsafe_allow_html=True)
with c6:
    if acc_val is not None:
        c = "#3b82f6" if acc_val>=0.8 else "#f97316" if acc_val>=0.6 else "#ef4444"
        st.markdown(badge("Accuracy", f"{acc_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge_empty("Accuracy", "verify text first"), unsafe_allow_html=True)
with c7:
    if rec_val is not None:
        c = "#6366f1" if rec_val>=0.8 else "#f97316" if rec_val>=0.6 else "#ef4444"
        st.markdown(badge("Recall", f"{rec_val:.3f}", c, "↻ live"), unsafe_allow_html=True)
    else:
        st.markdown(badge_empty("Recall", "verify text first"), unsafe_allow_html=True)

st.caption("↻ ROUGE-L, Accuracy, Recall update automatically after every verification")
st.markdown("---")

tab1, tab2 = st.tabs(["📊 Statistics", "📋 History"])

with tab1:
    if not ok_s: st.error("Cannot reach backend.")
    elif not history: st.info("No verifications yet — use sidebar.")
    else:
        live, _ = get(f"{API}/live_metrics")
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### Hallucination Score per Verification")
            df = pd.DataFrame(history[:50]).sort_values("id")
            df["run"] = range(1, len(df)+1)
            st.line_chart(
                df[["run","score"]].set_index("run").rename(columns={"score":"Halluc %"}),
                color="#ef4444")

        with col_right:
            st.markdown("### Live ROUGE-L per Verification")
            if live and live.get("per_verification"):
                per = [p for p in live["per_verification"] if p.get("rouge_l") is not None]
                if per:
                    df_r = pd.DataFrame(per)
                    df_r["run"] = range(1, len(df_r)+1)
                    chart = df_r[["run","rouge_l","running_avg_rouge_l"]].set_index("run")
                    chart.columns = ["ROUGE-L","Running Avg"]
                    st.line_chart(chart, color=["#6366f1","#10b981"])
                    avg = live.get("current_avg_rouge_l", 0)
                    st.caption(f"Average ROUGE-L: {avg:.3f} across {live['verifications_with_rouge']} corrections")
                else:
                    st.info("Verify a hallucinated text to see ROUGE-L chart")
            else:
                st.info("Verify texts to see live ROUGE-L")

with tab2:
    h2, ok2 = get(f"{API}/history?limit=200")
    if not ok2 or not h2: st.info("No history yet.")
    else:
        rows = []
        for r in h2:
            sc = r.get("score",0)
            rows.append({
                "Time":    r.get("created_at","")[:19].replace("T"," "),
                "Text":    r.get("input_text","")[:60]+"...",
                "Score %": sc,
                "Risk":    "🚨 High" if sc>=60 else "⚠️ Med" if sc>=40 else "🔶 Low" if sc>=20 else "✅ Clean",
                "Domain":  (r.get("subdomain") or "general").capitalize(),
                "ROUGE-L": f"{r['rouge_l']:.3f}" if r.get("rouge_l") else "—",
                "ms":      r.get("time_ms",0)
            })
        df = pd.DataFrame(rows)
        srch = st.text_input("Search:", placeholder="Filter text...")
        if srch: df = df[df["Text"].str.contains(srch, case=False, na=False)]
        st.dataframe(df, hide_index=True, use_container_width=True,
            column_config={"Score %": st.column_config.ProgressColumn(
                "Score %", min_value=0, max_value=100, format="%d%%")})
        with st.expander("Last verification detail"):
            last = h2[0]
            a, b = st.columns(2)
            with a:
                st.markdown("**Input:**")
                st.code(last.get("input_text",""), language="text")
            with b:
                st.markdown("**Corrected:**")
                st.code(last.get("corrected",""), language="text")
            st.write(f"Score: **{last.get('score',0)}%** | Domain: {last.get('subdomain','—')} | "
                     f"ROUGE-L: {last.get('rouge_l') or '—'} | Time: {last.get('time_ms',0)}ms")

st.markdown("---")
st.caption("ROUGE-L — Ji et al. (2022) · Precision/Recall/F1 — Mahawatta Dona et al. (2024)")
