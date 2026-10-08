# Speech Script — Jury / Defense Version (10-Minute Cut)
### "Trust, But Verify" (AIBThings 2026, Paper #465)

**This is the tightly-paced, real 10-minute version.** Every slide is now sized so no single slide runs long while others feel rushed — see the timing note at the end for the per-slide balance. Content is sourced only from the paper's own literature review, methodology, and results (Zeng et al.'s taxonomy, the paper's exact Gap A/Gap B names, and the verified 35–60% industry stat) — nothing from unverified figures sent earlier. For the full, unabridged version (~17–18 min, better suited to a longer thesis-defense slot with no strict time limit), see `Speech_Script_Complete_Detailed.md`.

⚠️ **Read the note under Slide 2 before presenting to a jury** — it explains why the industry stat below differs from what you originally sent me.

---

### Slide 1 — Title (0:00–0:29)

Good [morning/afternoon]. Honorable members of the jury, professors, and guests. I am Jaweher Hichri, presenting joint work with my co-author, Dr. Sameh Mansour, from Grand Valley State University. Our paper is titled "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:33–1:59)

Automotive engineers increasingly use large language models to draft code, interpret requirements, and support compliance with standards like ISO 26262 — to save time and money.

The problem: these models can hallucinate — confident, fluent answers that are simply wrong, with no sign of uncertainty. In a safety-critical field, that's a real compliance risk.

Three examples from our paper: a model invents the VSS signal path "Vehicle.Motor.Velocity" instead of the correct "Vehicle.Speed." It fabricates an ABS latency that doesn't match the certified spec. Or it invents "ASIL Z" — a level that doesn't exist; ISO 26262 defines only A through D.

> ⚠️ **Note on the statistic below:** the two figures you originally sent me ("$250 million/year" and "15–52%") don't match the paper's actual citations. The paper's real Joshi (2025) reference — published in *Preprints.org* — supports a **35–60% error-reduction** finding instead, which is what the sentence below uses. The "SQ Magazine" source is authored by B. Elad and is cited only for the 2-second latency target, not an error-rate range.

Hybrid RAG architectures — retrieval plus a language model, our design family — show a **35 to 60 percent reduction in hallucination errors** [Joshi, 2025]. To fix this, we classify errors by cause: **Data-Driven**, where the model never learned the fact, and **Reasoning-Driven**, where it has the facts but reasons incorrectly.

### Slide 3 — The Gap in Current Research (2:03–2:56)

This causal split comes from **Zeng et al.**, building on Ji et al.'s 2022 intrinsic/extrinsic taxonomy and Huang et al.'s 2024 factuality/faithfulness split. Of the fourteen papers we reviewed, only three touch the automotive domain directly — Pavel et al., Balu et al., and Mahawatta Dona et al. — each narrow to a single subdomain.

That leaves two gaps: **Gap A, the Subdomain Gap** — no benchmark spans all four automotive subdomains together — and **Gap B, the Usability Gap** — no real-time tool both detects and fixes these errors for practitioners.

### Slide 4 — What We Built (3:00–3:32)

To close these gaps, we built three things: the structured review itself; **The Verifier**, a real-time detection-and-correction pipeline delivered as a Chrome extension with a live dashboard; and a **300-case evaluation corpus** spanning all four subdomains at once. To be clear: this is a working system built on an established taxonomy, not a new detection algorithm.

### Slide 5 — A Seven-Stage Hybrid Pipeline (3:36–4:28)

The Verifier runs as seven stages. A rule layer checks twenty-five patterns and seven regular expressions in under a millisecond, at full precision. A TF-IDF search retrieves the five most relevant passages from our knowledge base. A Groq-accelerated language model then drafts a grounded correction in three to four hundred milliseconds. Where the rule layer already found a clear violation, it always overrides the model. Every correction is scored against its source passage with ROUGE-L to confirm it's grounded, then logged with a timestamp, and reflected instantly on a live dashboard.

### Slide 6 — System Architecture (4:32–5:10)

That logic maps onto four physical pieces. A **Chrome extension** is the engineer's front door; a **Streamlit dashboard** is the reporting side. Both talk to a single **FastAPI backend**, which fans each request out to the three engines you just heard about — all grounded in the same version-controlled, six-standard knowledge base. Every verdict is logged to **SQLite**, which is what feeds the dashboard's live metrics.

### Slide 7 — Ground Truth Fixed Before Any System Run (5:14–5:42)

A common flaw in this literature is grading a system against its own score. We avoided that: labels were fixed before any system run. The corpus has 300 cases, 75 per subdomain — 184 hallucinated, 116 correct controls — every label traced to a reference standard and independently auditable.

### Slide 8 — Results (5:46–6:06)

At our calibrated forty-percent threshold: accuracy 0.840, precision 0.972, recall 0.761, F1 0.854. That's 140 of 184 hallucinations caught, with only four false alarms, at a mean latency of 1.26 seconds — within our two-second target.

### Slide 9 — Per-Subdomain Results and Ablation (6:10–6:33)

Performance holds across subdomains, from 0.787 on electrical to 0.880 on mechanical and safety — no significant blind spot. Our ablation shows why the hybrid matters: rules alone give just 0.033 recall; adding the language-model judge raises that to 0.761.

### Slide 10 — A Threshold Recalibration, Reported Transparently (6:37–7:10)

One honest finding: our original fifty-percent threshold missed most true positives — only eleven cases, 0.060 recall. Recalibrating to forty percent raised that to 140 cases, 0.761 recall. We report this openly. Our limitations: the corpus uses fault injection rather than live model output, and a single annotator did the labeling — though every label is independently auditable.

### Slide 11 — How The Verifier Compares (7:14–8:07)

Set against SelfCheckGPT, AST-based validation, and naïve RAG, The Verifier is the only one of the four to cover both causal error categories, produce a verifiable, grounded repair, run under two seconds, and target automotive standards specifically. Our recall of 0.761 is lower than SelfCheckGPT's 91.43 percent, but that figure comes from a single subdomain at up to four seconds of latency — a simpler, single-category task. These are contextual comparisons, each measured on the original authors' own data, not a controlled re-run on our corpus; that re-run is planned future work.

### Slide 12 — Conclusion and Future Directions (8:11–8:47)

In summary: a deterministic rule engine neutralizes Data-Driven errors in under a millisecond with zero false alarms, while a retrieval-grounded language model handles Reasoning-Driven errors — in real time, inside the engineer's workflow. The Verifier reaches 0.840 accuracy, 0.972 precision, 0.761 recall, 0.854 F1. Next: dense retrieval, a local model, and extending this architecture to other safety-critical domains like aerospace and medical devices.

### Slide 13 — Q&A (8:51–8:57)

Thank you for your attention. I welcome the jury's questions.

---

## Timing Note

The spoken text above is **855 words** across 13 slides (added Slide 11, the Comparative Analysis table). At a deliberate 105 wpm plus pauses between slides, that's **~8:57 total** — comfortably under 10 minutes, with about a minute of margin for natural pacing, a slower moment, or an aside if a juror reacts to something. At a brisker 130 wpm it's a bit faster; at a slower 95 wpm, still comfortably under 10 since the pause overhead dominates at this length.

No single slide dominates — here's the per-slide split:

| Slide | Time |
|---|---|
| 1. Title | 0:29 |
| 2. Introduction & Motivation | 1:27 |
| 3. The Gap in Current Research | 0:53 |
| 4. What We Built | 0:32 |
| 5. Seven-Stage Pipeline | 0:52 |
| 6. System Architecture | 0:38 |
| 7. Ground Truth Fixed | 0:28 |
| 8. Results | 0:21 |
| 9. Subdomain Results & Ablation | 0:23 |
| 10. Threshold Recalibration | 0:33 |
| 11. How The Verifier Compares | 0:53 |
| 12. Conclusion | 0:36 |
| 13. Q&A | 0:06 |

The longest is Slide 2 at under a minute and a half; everything else is under a minute. If you'd rather use the full 10 minutes instead of leaving ~1 minute of margin, the two easiest places to add back detail are Slide 5 (name what each of the seven stages catches) or Slide 6 (say a sentence more about the knowledge base's six standards) — let me know and I'll expand either one.

## Prepared Responses for Likely Questions

- **"Where does the $250M figure come from?"** → It doesn't — see the flagged note on Slide 2. Cite the verified 35–60% figure instead, or say the number was a citation error you caught and corrected.
- **"How does your Data-Driven/Reasoning-Driven split relate to Ji et al. and Huang et al.?"** → "Ji et al.'s intrinsic/extrinsic split and Huang et al.'s factuality/faithfulness split classify errors by *what* went wrong. Zeng et al.'s Data-Driven/Reasoning-Driven split, which we build on, classifies errors by *why* — a missing fact versus a reasoning failure — which is what let us map each cause onto a distinct architectural layer."
- **"Why is recall only 0.76, when SelfCheckGPT reports over 90%?"** → "Mahawatta Dona et al. report 91.43% recall with SelfCheckGPT, but on a single subdomain at 1.5 to 4 seconds of latency per query. Our result covers four subdomains simultaneously, under two seconds — a harder task."
- **"Is this evaluation circular?"** → "No. Ground truth was fixed by construction, before any system run, and is never derived from the system's own score."
- **"Who assigned the ground-truth labels?"** → "A single annotator, the first author — stated explicitly as a limitation. Every label is independently verifiable against a published standard."
- **"Is the system currently containerized or deployed on Kubernetes?"** → "The current implementation runs as the single-service architecture I just showed, which I can demonstrate. Containerized deployment is planned future work, not the present configuration."
- **"What was your ROUGE-L result?"** → "ROUGE-L is real and it is used — it's Stage 5 of the pipeline, computed live on every request to score the lexical overlap between the generated correction and the knowledge-base passage it's grounded in. What we don't do is report it as a corpus-level result. Section IV's evaluation — accuracy, precision, recall, F1, against the 300-case labeled corpus — doesn't include an aggregate ROUGE-L number; that's a different metric measured for a different purpose, per-response grounding rather than corpus-level detection performance. We chose ROUGE-L over BERTScore, which is too slow for real-time use, and over FActScore, which checks claims against Wikipedia — the wrong reference authority for ISO 26262 or AUTOSAR content. Reporting the ROUGE-L distribution across the full corpus as its own quantitative result is a natural next step, not something we did in this paper."
