"""
Backfill an evaluation row from existing history.
Run once: python fix_rouge.py

Uses the SAME two-threshold decoupled protocol as server.py:
  Ground truth: score >= 40  (truly hallucinated)
  Prediction:   score >= 50  (system raised a warning)
The 40-49 gap produces genuine False Negatives, so Recall < 1.000.

NOTE: because both labels derive from the pipeline score, FP is 0 by
construction here. Real FP counts come from the manual expert labeling
described in the thesis (Chapter 9). This script only refreshes the live
monitoring metrics — it is not the published evaluation.
"""
import sqlite3, datetime
from pathlib import Path

BASE    = Path(__file__).parent
DB_FILE = BASE / "history.db"

GT_THRESHOLD   = 40   # ground truth: truly hallucinated
PRED_THRESHOLD = 50   # prediction: system warns

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, score, rouge_l FROM history ORDER BY id ASC").fetchall()
rouge_vals = [r["rouge_l"] for r in rows if r["rouge_l"] is not None]
avg_rouge  = round(sum(rouge_vals) / len(rouge_vals), 4) if rouge_vals else 0.0

if len(rows) >= 4:
    tp = fp = tn = fn = 0
    for r in rows:
        true_val = 1 if r["score"] >= GT_THRESHOLD   else 0
        pred_val = 1 if r["score"] >= PRED_THRESHOLD else 0
        if   true_val == 1 and pred_val == 1: tp += 1
        elif true_val == 0 and pred_val == 1: fp += 1
        elif true_val == 0 and pred_val == 0: tn += 1
        else:                                 fn += 1

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    acc  = (tp + tn) / len(rows)

    conn.execute(
        "INSERT INTO evaluations (created_at,rouge_l,f1_score,precision,recall,accuracy,total) VALUES (?,?,?,?,?,?,?)",
        (datetime.datetime.now().isoformat(), avg_rouge,
         round(f1, 4), round(prec, 4), round(rec, 4), round(acc, 4), len(rows))
    )
    conn.commit()
    print(f"\nEvaluated {len(rows)} records:")
    print(f"  Accuracy: {acc:.3f} | Recall: {rec:.3f} | F1: {f1:.3f}")
    print(f"  TP={tp}  FP={fp}  TN={tn}  FN={fn}")
    print(f"  Avg ROUGE-L: {avg_rouge:.4f}")
else:
    print("Not enough history rows (need at least 4).")

conn.close()
print("\nDone! Restart server.py and refresh the dashboard.")
