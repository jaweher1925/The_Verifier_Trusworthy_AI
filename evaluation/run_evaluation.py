"""
run_evaluation.py — reviewer-response evaluation for The Verifier.

Runs the 104 labeled cases in evaluation_dataset.json through the system and
produces everything the AIBThings2026 reviewers asked for:
  * exact confusion matrix (TP/FP/TN/FN) against HUMAN ground-truth labels
    (independent of the system score -> no circularity)
  * accuracy / precision / recall / F1 with 95% Wilson confidence intervals
  * per-subdomain breakdown
  * ablation: rules-only (S1) vs full pipeline (S1+S3)
  * list of misses (FN) and false alarms (FP) for the failure analysis

Usage:
  python run_evaluation.py --mode rules            # offline, no API needed
  python run_evaluation.py --mode full             # needs backend on :8000
  python run_evaluation.py --mode both             # runs both + comparison

The prediction rule matches the paper: predicted hallucinated iff score >= 50.
"""
import argparse, json, math, sys, time, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "evaluation_dataset.json")
ALERT_THRESHOLD = 40   # calibrated operating point (paper Sec. IV)

def wilson(p, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c-m)/d, (c+m)/d)

def score_rules(text):
    """S1 only: import the detector straight from server.py (offline)."""
    sys.path.insert(0, os.path.join(HERE, "backend"))
    global _detect
    try:
        _detect
    except NameError:
        os.environ.setdefault("GROQ_API_KEY", "offline")
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "server", os.path.join(HERE, "backend", "server.py"))
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print("could not import server.py:", e); raise
        _detect = mod.detect
    return _detect(text)["score"]

CACHE_FILE = os.path.join(HERE, "judge_score_cache.json")
def _load_cache():
    try: return json.load(open(CACHE_FILE))
    except Exception: return {}
def _save_cache(c): json.dump(c, open(CACHE_FILE, "w"), indent=0)

_cache = _load_cache()

def score_full(text, case_id=None):
    """Full pipeline via the running backend.
    - Successful judge scores are cached in judge_score_cache.json, so an
      interrupted or rate-limited run can be resumed without re-spending quota.
    - Retries twice on judge errors (rate limit); if still failing, raises
      QuotaExhausted so the run stops cleanly instead of polluting results."""
    key = str(case_id)
    if key in _cache:
        return _cache[key]
    import urllib.request
    resp = None
    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(
            "http://localhost:8000/verify",
            data=json.dumps({"text": text}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.load(r)
        if "LLM error" not in resp.get("reason", ""):
            _cache[key] = resp["score"]
            _save_cache(_cache)
            print(f"    case #{case_id} done ({len(_cache)}/300 cached)")
            time.sleep(2)
            return resp["score"]
        if "429" in resp.get("reason", ""):
            print(f"    quota wall at case #{case_id} ({len(_cache)}/300 cached) -> auto-wait 10 min...")
            time.sleep(600)
        else:
            wait = min(30 * attempt, 120)
            print(f"    judge error ({resp['reason'][:70]}...) -> retry in {wait}s")
            time.sleep(wait)

class QuotaExhausted(Exception):
    pass

def evaluate(cases, scorer, name):
    tp = fp = tn = fn = 0
    per_sub = defaultdict(lambda: [0,0,0,0])   # tp fp tn fn
    misses, alarms = [], []
    t0 = time.time()
    for c in cases:
        try:
            s = scorer(c["text"], c["id"]) if scorer is score_full else scorer(c["text"])
        except QuotaExhausted as e:
            print(f"\nSTOPPED: {e}")
            print("Run the same command again after the quota resets - cached cases are skipped.")
            sys.exit(1)
        pred = 1 if s >= ALERT_THRESHOLD else 0
        gt = c["gt_label"]
        k = per_sub[c["subdomain"]]
        if   gt==1 and pred==1: tp+=1; k[0]+=1
        elif gt==0 and pred==1: fp+=1; k[1]+=1; alarms.append((c["id"], s, c["text"][:60]))
        elif gt==0 and pred==0: tn+=1; k[2]+=1
        else:                   fn+=1; k[3]+=1; misses.append((c["id"], s, c["band"], c["text"][:60]))
    n = len(cases)
    acc = (tp+tn)/n
    prec = tp/(tp+fp) if tp+fp else 0
    rec  = tp/(tp+fn) if tp+fn else 0
    f1   = 2*prec*rec/(prec+rec) if prec+rec else 0
    lo, hi = wilson(acc, n)
    rlo, rhi = wilson(rec, tp+fn) if tp+fn else (0,0)
    print(f"\n===== {name} (n={n}, {time.time()-t0:.1f}s) =====")
    print(f"Confusion: TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Accuracy  {acc:.3f}  (95% CI {lo:.3f}-{hi:.3f})")
    print(f"Precision {prec:.3f}   Recall {rec:.3f} (95% CI {rlo:.3f}-{rhi:.3f})   F1 {f1:.3f}")
    print("Per subdomain (TP/FP/TN/FN, acc):")
    for sub, (a,b,cn,d) in sorted(per_sub.items()):
        tot = a+b+cn+d
        print(f"  {sub:<11} {a:>2}/{b:>2}/{cn:>2}/{d:>2}  acc={(a+cn)/tot:.3f}")
    if misses:
        print("False negatives (missed):")
        for i, s, band, t in misses: print(f"  #{i:<3} score={s:<3} band={band:<10} {t}")
    if alarms:
        print("False positives (false alarms):")
        for i, s, t in alarms: print(f"  #{i:<3} score={s:<3} {t}")
    return {"name":name,"n":n,"tp":tp,"fp":fp,"tn":tn,"fn":fn,"accuracy":acc,
            "precision":prec,"recall":rec,"f1":f1,"acc_ci":[lo,hi]}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["rules","full","both"], default="rules")
    args = ap.parse_args()
    cases = json.load(open(DATASET))
    results = []
    if args.mode in ("rules","both"):
        results.append(evaluate(cases, score_rules, "S1 rules-only (ablation)"))
    if args.mode in ("full","both"):
        results.append(evaluate(cases, score_full, "Full pipeline (S1+S3)"))
    out = os.path.join(HERE, "evaluation_results.json")
    json.dump(results, open(out,"w"), indent=1)
    print(f"\nSaved -> {out}")
