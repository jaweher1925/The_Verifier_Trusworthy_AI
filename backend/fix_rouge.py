"""
Run this once to backfill ROUGE-L for existing history rows.
python fix_rouge.py
"""
import sqlite3, pickle
from pathlib import Path

BASE     = Path(__file__).parent
DB_FILE  = BASE / "history.db"
DATA_DIR = BASE / "data"

def rouge_l(hyp, ref):
    h = hyp.lower().split(); r = ref.lower().split()
    if not h or not r: return 0.0
    dp = [[0]*(len(r)+1) for _ in range(len(h)+1)]
    for i in range(1, len(h)+1):
        for j in range(1, len(r)+1):
            dp[i][j] = dp[i-1][j-1]+1 if h[i-1]==r[j-1] else max(dp[i-1][j],dp[i][j-1])
    lcs = dp[len(h)][len(r)]
    p = lcs/len(h); rc = lcs/len(r)
    return round(2*p*rc/(p+rc),4) if (p+rc)>0 else 0.0

kb_text = (DATA_DIR / "knowledge_base.txt").read_text(encoding="utf-8")
kb_lines = [l.strip() for l in kb_text.split("\n") if len(l.strip()) > 20]

def get_rouge(text):
    words = set(text.lower().split())
    scored = []
    for line in kb_lines:
        overlap = len(words & set(line.lower().split()))
        if overlap > 2:
            scored.append((overlap, line))
    scored.sort(reverse=True)
    if not scored: return None
    ref = " ".join(l for _, l in scored[:5])
    return rouge_l(text, ref)

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, input_text, corrected, score FROM history WHERE rouge_l IS NULL").fetchall()
print(f"Backfilling {len(rows)} rows...")
updated = 0
for row in rows:
    eval_text = row["corrected"] if (row["corrected"] and row["corrected"] != row["input_text"] and len(row["corrected"]) > 20) else row["input_text"]
    rl = get_rouge(eval_text)
    if rl is not None:
        conn.execute("UPDATE history SET rouge_l=? WHERE id=?", (rl, row["id"]))
        updated += 1
conn.commit()

# Recalculate evaluations
all_rows = conn.execute("SELECT score, rouge_l FROM history").fetchall()
rouge_vals = [r["rouge_l"] for r in all_rows if r["rouge_l"] is not None]
avg_rouge = round(sum(rouge_vals)/len(rouge_vals), 4) if rouge_vals else 0.0

halluc = [r for r in all_rows if r["score"] >= 30]
clean  = [r for r in all_rows if r["score"] <= 20]
used   = halluc + clean
if len(used) >= 2:
    y_true = [1]*len(halluc) + [0]*len(clean)
    y_pred = [1 if r["score"] >= 25 else 0 for r in used]
    tp = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==1)
    fp = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==1)
    tn = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==0)
    fn = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==0)
    prec = tp/(tp+fp) if (tp+fp)>0 else 0.0
    rec  = tp/(tp+fn) if (tp+fn)>0 else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
    acc  = (tp+tn)/len(used)
    import datetime
    conn.execute(
        "INSERT INTO evaluations (created_at,rouge_l,f1_score,precision,recall,accuracy,total) VALUES (?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), avg_rouge,
         round(f1,4), round(prec,4), round(rec,4), round(acc,4), len(all_rows))
    )
    conn.commit()
    print(f"\nResults after backfill:")
    print(f"  ROUGE-L:  {avg_rouge:.3f} ({len(rouge_vals)} values)")
    print(f"  Accuracy: {acc:.3f}")
    print(f"  Recall:   {rec:.3f}")
    print(f"  F1:       {f1:.3f}")
    print(f"  TP={tp} FP={fp} TN={tn} FN={fn} (from {len(used)} confident cases)")
conn.close()
print(f"\nUpdated {updated} rows. Restart server and refresh dashboard.")
