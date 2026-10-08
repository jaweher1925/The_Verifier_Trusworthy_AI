# Speech Script — Complete Detailed Version (13 Slides)
### "Trust, But Verify" (AIBThings 2026, Paper #465)

**This is the single, complete, full-detail script** — no content trimmed for time. It covers all 13 slides of `Verifier_Jury_Defense_Presentation.pptx`, includes the full jury address, the industry-impact framing, the complete hallucination-taxonomy lineage (Ji et al. → Huang et al. → Zeng et al.), a full stage-by-stage pipeline walkthrough, **a dedicated, explicit walkthrough of the system architecture** (Slide 6) matching the architecture diagram in the deck — frontend, backend, the three pipeline components, storage, and dashboard, all named and connected — and a full **Comparative Analysis** (Slide 11) against SelfCheckGPT, AST validation, and naïve RAG, straight from the paper's own Section IV.D. See the timing note at the end for exact word count and pacing; at this level of detail it will run longer than the shortened version I sent earlier, so budget accordingly or use it for a setting with a longer time allowance (e.g. a full thesis defense rather than a 15-minute conference slot).

⚠️ **Read the note under Slide 2 before presenting to a jury** — two industry statistics you originally sent me didn't match the paper's own citations. The paragraph below already uses the verified figure; the note explains why.

---

### Slide 1 — Title (0:00–0:29)

Good [morning/afternoon]. Honorable members of the jury, professors, and guests. I am Jaweher Hichri, presenting joint work with my co-author, Dr. Sameh Mansour, from Grand Valley State University. Our paper is titled "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:33–3:17)

Automotive engineers increasingly rely on large language models to draft code, interpret requirements, and support compliance with standards such as ISO 26262 — to save time and money. This is becoming a normal part of engineering work, not an exception.

The difficulty is that these models can hallucinate: they produce confident, fluent answers that are simply wrong. They do not sound uncertain when they are wrong. In a safety-critical field, that is not a minor issue — it is a real compliance risk.

Consider three concrete examples straight from our paper's introduction. A model may invent a nonexistent COVESA VSS signal path — for instance, fabricating "Vehicle.Motor.Velocity" in place of the correct "Vehicle.Speed." It may fabricate an Anti-lock Braking System latency that does not match the certified specification. Or it may conjure a fake Automotive Safety Integrity Level, such as "ASIL Z" — a level that does not exist; ISO 26262 defines only A through D.

From an industry perspective, this problem is both financial and operational, and it shows up directly in error rates across the field.

> ⚠️ **Note on the statistic below — please read before presenting:**
> I checked the paper's own bibliography for the two figures you originally sent me ("$250 million/year," attributed to Joshi on SSRN; "15% to 52%," attributed to "Magazine, S. Q."), and neither matched as written:
> - The paper's actual Joshi (2025) reference is published in *Preprints.org*, not SSRN, and is cited for a **35–60% error-reduction** finding for hybrid RAG architectures — not a dollar-loss figure. I could not find a "$250 million/year" number anywhere in the paper.
> - The "SQ Magazine, 2026" source is authored by **B. Elad** (SQ Magazine is the publication, not the author's surname — "Magazine, S. Q." is a citation-formatting mix-up), and the paper cites it only to justify the 2-second real-time latency target, not a 15–52% error-rate range.
> The paragraph below uses the verified 35–60% figure. Please confirm before presenting to a jury, or ask me to drop the stat entirely if you'd rather not cite it.

Recent literature offers a verifiable data point here: hybrid RAG architectures — combining retrieval with a language model, the same design family as ours — show a **35 to 60 percent reduction in hallucination errors** across numerous deployments [Joshi, 2025]. That is the scale of the problem we are addressing, and the scale of what a well-designed hybrid system can recover.

To solve this, we must first understand why these models fail. Our research categorizes these errors into two distinct roots: **Data-Driven errors**, where the model never properly learned the correct fact, and **Reasoning-Driven errors**, where the model has all the correct facts but makes a logic error combining them.

### Slide 3 — The Gap in Current Research (3:21–6:30)

This causal framing is not our own invention — our paper traces it through a specific line of prior research on why language models hallucinate.

In 2022, Ji et al. proposed a foundational taxonomy: **intrinsic** hallucinations, which directly contradict a provided source, and **extrinsic** hallucinations, which introduce unverifiable external information. In 2024, Huang et al. adapted this for modern generative models, reframing it as **factuality** — does the text contradict real-world facts — and **faithfulness** — does the text stay true to the given source.

Our paper adopts a third, causal taxonomy instead — proposed by **Zeng et al.** — which asks not just *what kind* of error occurred, but *why*. **Data-Driven errors** come from gaps in the model's training data: automotive-specific facts, like an internal OEM guideline or a specialized ISO clause, are simply underrepresented in general training data, so the model defaults to something statistically plausible but wrong. **Reasoning-Driven errors** happen when the model already has the correct facts, but fails to combine them correctly during inference — for example, knowing what ASIL D requires, but assigning it to a component without the mandatory hazard analysis and risk assessment. This causal distinction is what let us map each error type onto a different layer of our architecture: Data-Driven errors are caught by exact deterministic lookups, while Reasoning-Driven errors need a language model's contextual judgment.

Of the fourteen papers we reviewed, only three tackle the automotive domain directly, and each is narrow. Pavel et al. focus on VSS code generation without a real-time detection mechanism. Balu et al. use agent-based RAG for safety requirements but omit post-generation verification. Mahawatta Dona et al. apply SelfCheckGPT to ADAS perception, but at high latency and in only one subdomain. That fragmentation is exactly what defines our two gaps: **Gap A, the Subdomain Gap** — no benchmark evaluates all four automotive subdomains together — and **Gap B, the Usability Gap** — no deployable, real-time tool actually detects, tests, and fixes these errors for practitioners.

### Slide 4 — What We Built (6:34–7:23)

To address these gaps, we developed three contributions. First, the structured review itself, which makes these two gaps explicit. Second, The Verifier: a real-time detection-and-correction pipeline, delivered as a Chrome extension with a live dashboard, so it fits into an engineer's normal workflow. Third, a 300-case evaluation corpus, the first of its kind to span all four subdomains at once.

To be precise, our contribution is not a new detection algorithm — it is a working system, built on an established hallucination taxonomy, and evaluated rigorously.

### Slide 5 — A Seven-Stage Hybrid Pipeline (7:27–10:38)

At a high level, the system combines two layers. First, a fast, deterministic rule layer checks the text against known invalid facts, in under one millisecond, with perfect precision. Second, a language model, grounded in our knowledge base, reviews anything the rules do not catch, and drafts a correction. When the rule layer finds a clear violation, its verdict always takes priority over the language model's judgment. This combination is what lets the system stay both fast and reliable.

Let us now look at the core technical engine of our project. The Verifier runs in seven stages — a hybrid Retrieval-Augmented Generation pipeline that handles everything from the initial input to the final verified output in one unified flow. Let me walk you through it, step by step.

**Stage 1 — Pattern Detection:** we compare the input against twenty-five static rules and seven context-aware regular expressions — catching invalid signal paths, impossible safety levels, and similar known errors in under one millisecond, with one hundred percent precision on that rule set.

**Stage 2 — Knowledge Search:** we perform a fast TF-IDF search across our six official automotive standards, retrieving the five most relevant reference passages in a few milliseconds.

**Stage 3 — AI Model:** accelerated by Groq, a language model reviews the input against those retrieved passages and drafts a grounded correction, in three hundred to four hundred milliseconds.

**Stage 4 — Asymmetric Fusion:** we combine both layers' verdicts. If Stage 1 already found a clear, deterministic violation, that verdict always overrides the language model's judgment.

**Stage 5 — ROUGE-L Evaluation:** we score the proposed correction against the retrieved knowledge-base passage using ROUGE-L, proving the correction is factually grounded — not merely fluent.

**Stage 6 — Storage:** every transaction — the original prompt, the safety scores, the factual correction, and a timestamp — is saved permanently in our secure database.

**Stage 7 — Dashboard:** our live Streamlit interface updates instantly, giving engineering teams real-time visibility into system health, accuracy, recall, and historical metrics.

### Slide 6 — System Architecture, End to End (10:42–13:36)

Having walked through the seven logical stages, let me now show you how they are actually deployed as a system — this is the architecture diagram you see on screen.

On the front end, engineers interact with the system through a **Chrome extension**, built on Manifest V3, that lets them highlight any AI-generated text and verify it in place. On the reporting side, a **Streamlit dashboard** gives quality teams a live view of accuracy, recall, and the full audit trail.

Both of those talk to a single **FastAPI backend**, exposing two endpoints — `/verify` for a live check, and `/history` for the audit log. The backend is the hub: it receives a verification request from the extension, fans it out to the three core engines, and returns the combined verdict.

Those three engines sit in the middle layer. The **S1 rule engine** applies our twenty-five patterns and seven regular expressions in under a millisecond. The **S2 TF-IDF index** searches our 146-entry knowledge base, spanning six automotive standards, for the most relevant passages. The **S3 RAG judge** — our Groq-served language model — reasons over those retrieved passages to draft a grounded correction in three to four hundred milliseconds. Both S2 and S3 draw directly from the same knowledge base at the bottom of the diagram: COVESA VSS, ISO 26262, SOTIF, SAE J1979, and AUTOSAR, version-controlled with DVC so it can be updated as standards evolve, alongside HaluEval for general-purpose hallucination patterns.

Every verdict, from every stage, is written to a **SQLite** history database — stage six of the pipeline — which is what powers the dashboard's live metrics and gives us a permanent, independently reviewable audit trail. In short: one browser-based front door, one backend hub, three specialized reasoning engines grounded in a shared, versioned knowledge base, and one persistent log underneath all of it.

### Slide 7 — Ground Truth Fixed Before Any System Run (13:40–14:39)

Now, evaluation methodology — and this is a point we care about deeply. A common flaw in this literature is using a system's own score to both define ground truth and grade performance, which effectively grades the system against itself.

To eliminate that circularity, our labels were fixed by construction, before any system run. The corpus contains 300 cases, seventy-five per subdomain: 184 hallucinated statements — 140 clearly corrupted facts and 44 borderline, hedged variants — alongside 116 correct control statements. Every label traces to one of our six reference standards, making the evaluation independently auditable rather than dependent on a single reviewer's judgment.

### Slide 8 — Results (14:43–15:21)

At our calibrated forty-percent alert threshold, across all 300 cases, the system achieves an accuracy of 0.840, a precision of 0.972, a recall of 0.761, and an F1 score of 0.854. In concrete terms, it correctly identifies 140 of 184 hallucinations, with only four false alarms among 116 correct statements. Mean latency in the deployed configuration is 1.26 seconds, comfortably within our two-second real-time target.

### Slide 9 — Per-Subdomain Results and Ablation (15:25–16:10)

Performance is consistent across subdomains, with accuracy ranging from 0.787 on electrical to 0.880 on mechanical and safety — indicating no significant blind spot.

Our ablation study addresses a direct question: is the hybrid design necessary? Using the rule layer alone yields only 0.033 recall, though with zero false positives. Adding the language-model judge raises recall to 0.761. This confirms that the language model provides the majority of detection coverage, while the rule layer's role is to preserve precision.

### Slide 10 — A Threshold Recalibration, Reported Transparently (16:14–17:17)

One further finding deserves mention. On inspection, the judge's scoring consistently concentrated single-violation detections around forty-five percent. Our original fifty-percent alert threshold therefore missed a substantial share of true positives, catching only eleven cases, for a recall of 0.060. Recalibrating to forty percent raised that figure to 140 cases and a recall of 0.761.

We report this openly, as a diagnosed and corrected calibration effect, rather than presenting only the favorable outcome. We also state our limitations plainly: the corpus was constructed through deliberate fault injection rather than harvested from live model output, and labeling was performed by a single annotator, though every label is independently auditable against a published standard.

### Slide 11 — How The Verifier Compares (17:21–19:16)

Our paper's evaluation section closes with a direct comparative analysis, and it's worth walking through carefully, because it draws an honest line between what we can claim and what we can't.

Benchmarked conceptually against SelfCheckGPT, AST-based code validation, and naïve Retrieval-Augmented Generation, The Verifier is the only one of these four approaches to encompass both causal hallucination categories, provide a verifiable, grounded repair rather than a bare flag, execute within our two-second real-time target, and explicitly target automotive standards. Our recall of 0.761 is lower than SelfCheckGPT's reported 91.43 percent, but that comparison needs context: SelfCheckGPT's figure comes from a single subdomain, ADAS perception, at one-and-a-half to four seconds of latency per query — a simpler, single-category task next to our four-subdomain, sub-two-second target. AST-based validation reaches 100 percent precision and 87.6 percent recall, but only on code, and cannot process natural-language safety requirements at all.

We are explicit that these are contextual comparisons, not a controlled benchmark: each baseline figure is measured on the original authors' own dataset, not on a re-run against our corpus. Running SelfCheckGPT, AST validation, and naïve RAG directly against our 300-case corpus is planned future work, not something this paper claims to have already done.

### Slide 12 — Conclusion and Future Directions (19:20–20:13)

In summary: a deterministic rule engine neutralizes Data-Driven errors in under one millisecond with zero false alarms, while a retrieval-grounded language-model judge addresses Reasoning-Driven errors and drafts standards-backed corrections — all operating in real time, within the engineer's existing workflow.

Evaluated against an independent, standards-traced ground truth, The Verifier achieves 0.840 accuracy, 0.972 precision, 0.761 recall, and an F1 score of 0.854. Planned extensions include dense vector retrieval, a locally hosted model to remove dependence on external APIs, and generalization of this architecture to other safety-critical domains such as aerospace and medical devices.

### Slide 13 — Q&A (20:17–20:23)

Thank you for your attention. I welcome the jury's questions.

---

## Literature-Review Correction (this revision)

You asked me to use only what's actually in the paper's literature review for this section, not the material you'd pasted earlier. Two things changed on **Slide 2** and **Slide 3**:

- **The ABS example on Slide 2** no longer states specific numbers ("1 ms" vs. "50–150 ms"). I checked `paper_camera.tex` directly — it only says a model may "fabricate an Anti-lock Braking System (ABS) latency," with no numeric range anywhere in the paper. I removed the invented figures rather than repeat them in front of a jury.
- **Slide 3 is now sourced directly from the paper's "Background and Related Work" section**, not the version you sent me. It now: names **Zeng et al.** explicitly as the source of the Data-Driven/Reasoning-Driven split (the paper's own wording, including the ASIL-D/HARA reasoning example); uses the paper's exact gap names, **Gap A (the Subdomain Gap)** and **Gap B (the Usability Gap)**; and names the three automotive-specific studies the paper actually reviews — **Pavel et al.** (VSS code generation), **Balu et al.** (agentic RAG for safety requirements), and **Mahawatta Dona et al.** (SelfCheckGPT on ADAS perception) — instead of a generic "14 papers reviewed" line.

Everything else (the taxonomy examples for Ji et al. and Huang et al., the verified 35–60% stat, the seven-stage pipeline, the architecture walkthrough, and all results) was already checked against the paper in earlier passes and is unchanged.

## Timing Note

The spoken text above is **2,056 words** (up from 1,855 — added Slide 11, the Comparative Analysis, ~201 words). At a slower, deliberate 105 wpm — the pace I'd recommend for a jury/defense setting — plus pauses at the 12 transitions between the 13 slides, the per-slide timestamps above already total **~20:23**.

Four slides now dominate the runtime: **Slide 3** (the gap analysis, ~3:10), **Slide 5** (the seven-stage pipeline, ~3:10), **Slide 6** (the system architecture, ~2:55), and **Slide 11** (the new comparative analysis, ~1:55). If this needs to fit a strict time slot, those four are the highest-impact places to trim; otherwise, this version is best suited to a thesis defense or any setting with a longer allowance. Let me know your actual time limit and I can retime precisely.

## Prepared Responses for Likely Questions

- **"Where does the $250M figure come from?"** → Be ready to cite the real source precisely, or drop the figure — see the flagged note on Slide 2.
- **"How does your Data-Driven/Reasoning-Driven split relate to Ji et al. and Huang et al.?"** → "Ji et al.'s intrinsic/extrinsic split and Huang et al.'s factuality/faithfulness split classify errors by *what* went wrong. Zeng et al.'s Data-Driven/Reasoning-Driven split, which we build on, classifies errors by *why* — a missing fact versus a reasoning failure — which is what let us map each cause onto a distinct architectural layer."
- **"Walk me through what happens if the rule engine and the language model disagree."** → "The rule engine only fires on twenty-five hand-verified patterns, so when it fires, it is always right by construction — its verdict overrides the model's. The language model handles everything the rules don't cover, which is the majority of real-world cases."
- **"Why is recall only 0.76, when SelfCheckGPT reports over 90%?"** → "SelfCheckGPT is evaluated on a single subdomain with 1.5 to 4 seconds of latency per query. Our result covers four subdomains simultaneously, under two seconds — a harder task, and the comparison in the paper is contextual, not a controlled re-run."
- **"Is this evaluation circular?"** → "No. Ground truth was fixed by construction, before any system run, and is never derived from the system's own score."
- **"Who assigned the ground-truth labels?"** → "A single annotator, the first author — stated explicitly as a limitation. Every label is independently verifiable against a published standard."
- **"Is the system currently containerized or deployed on Kubernetes?"** → "The current implementation runs as the single-service architecture I just showed, which I can demonstrate. Containerized deployment is planned future work, not the present configuration."
- **"What was your ROUGE-L result?"** → "ROUGE-L is real and it is used — it's Stage 5 of the pipeline, computed live on every request to score the lexical overlap between the generated correction and the knowledge-base passage it's grounded in. What we don't do is report it as a corpus-level result. Section IV's evaluation — accuracy, precision, recall, F1, against the 300-case labeled corpus — doesn't include an aggregate ROUGE-L number; that's a different metric measured for a different purpose, per-response grounding rather than corpus-level detection performance. We chose ROUGE-L over BERTScore, which is too slow for real-time use, and over FActScore, which checks claims against Wikipedia — the wrong reference authority for ISO 26262 or AUTOSAR content. Reporting the ROUGE-L distribution across the full corpus as its own quantitative result is a natural next step, not something we did in this paper."
