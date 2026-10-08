# Speech Script — "Trust, But Verify" (AIBThings 2026, Paper #465)

**Target: ~11 minutes presentation + 2–4 minutes Q&A, inside the 15-minute slot.**
Read it once out loud with a timer before the session — this script is paced for a natural speaking rate (~130 wpm), not a fast read. Sentences marked *(optional)* can be cut if you're running long, without breaking the flow.

---

### Slide 1 — Title (0:00–0:30)

Good [morning/afternoon] everyone. I'm Jaweher Hichri, and together with my co-author Dr. Sameh Mansour at Grand Valley State University, I'll be presenting our paper, "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:30–1:50)

Automotive engineers are increasingly using large language models — GPT-4, Claude, LLaMA — to draft code, parse requirements, and check compliance with standards like ISO 26262.

The problem is that these models hallucinate. They don't fail loudly — they generate text that is fluent, confident, and simply wrong. And in a safety-critical domain, that's not a minor inconvenience — it's a compliance risk.

These are the same three examples our paper opens with, in the Introduction. First, an invented VSS signal path, "Vehicle-dot-Motor-dot-Velocity," when the real one — per the COVESA VSS 4.0 specification — is "Vehicle-dot-Speed." Second, a claim that ABS responds in 1 millisecond, when the validated range our knowledge base encodes is 50 to 150. And third, "ASIL Z" — which sounds plausible, but simply doesn't exist; ISO 26262:2018 defines only A through D.

*(optional)* That same VSS example reappears later, in Section IV, where it illustrates how we constructed our 300-case evaluation corpus. And similar VSS-related hallucinations in automotive code generation have also been reported by Pavel et al.

What makes automotive engineering a good target for this problem is that a lot of its critical facts are finite and formally enumerable — the valid VSS paths, the four ASIL levels, the OBD-II parameter IDs. That means a real share of hallucinations here can be checked deterministically, against a published standard, rather than only judged for plausibility.

### Slide 3 — The Gap in Current Research (1:50–2:50)

We reviewed 14 papers on LLM hallucination published between 2022 and 2026, and found two open gaps.

Gap A: no existing benchmark evaluates hallucinations across all four automotive subdomains — mechanical, electrical, software, and safety — at the same time. Every prior automotive study picks one slice.

Gap B: no deployable, real-time tool actually detects, tests, *and* fixes these errors. SelfCheckGPT gets strong recall but takes 1.5 to 4 seconds per check — too slow for interactive use. AST-based parsing is fast and precise, but only works on code, not natural language.

### Slide 4 — What We Built (2:50–3:50)

That leads to our three contributions. First, the structured review itself, exposing those two gaps. Second, The Verifier — an end-to-end, real-time pipeline that plugs into the engineer's existing workflow through a Chrome extension and a live Streamlit dashboard. And third, the first cross-subdomain, standards-traced 300-case evaluation corpus in this literature.

I want to be precise about what kind of contribution this is: it is not a new detection algorithm. It's a deployable mapping of an existing causal hallucination taxonomy onto a working, two-layer architecture — plus the evaluation methodology to actually measure it honestly.

### Slide 5 — A Seven-Stage Hybrid Pipeline (3:50–5:10)

Here's how a request actually moves through the system. Stage 1 is a local, deterministic pattern layer — twenty-five rules and seven context-aware regular expressions that catch invalid VSS paths, impossible ASIL levels, and similar errors in under a millisecond, with 100% precision on that rule set.

Stage 2 retrieves the five most relevant knowledge-base entries using TF-IDF, in about 5 milliseconds. Stage 3 is where an LLM judge — served on Groq — evaluates the input against that retrieved context and drafts a grounded correction, in 300 to 400 milliseconds.

Stage 4 is decision fusion: if Stage 1 already found a critical, deterministic violation, that verdict always overrides the LLM's judgment. Stages 5 through 7 handle grounding quality, persistence, and the live dashboard metrics.

The key design idea: deterministic checks run first and are trusted completely; the probabilistic judge only handles what survives them. This maps directly onto the two root causes of hallucination we drew from prior work: data-driven errors, where the model never learned a fact and defaults to something plausible-sounding, and reasoning-driven errors, where the model knows the right pieces but fails to connect them correctly — for example assigning ASIL D without ever checking that a hazard analysis was done.

### Slide 6 — Grounded in Six Automotive Standards (5:10–6:05)

None of this works without a grounded knowledge base. We curated 146 entries from six authoritative sources — COVESA VSS 4.0, ISO 26262, SOTIF, SAE J1979, AUTOSAR, and HaluEval's linguistic patterns. Every entry is bidirectional: it states the correct fact *and* the common hallucinated variant, side by side.

We deliberately chose TF-IDF over dense embeddings — no GPU needed, sub-5-millisecond retrieval, and the index rebuilds in minutes whenever a standard is updated. The backend is a single FastAPI service; the Chrome extension is the frontend; the dashboard tracks live QA metrics for audit purposes.

### Slide 7 — Ground Truth Fixed Before Any System Run (6:05–7:05)

Now, evaluation methodology — and this is a point we care about a lot. A common flaw in this kind of work is using the system's own risk score both to define ground truth *and* to grade performance — which grades a system against itself.

To avoid that entirely, our 300-case corpus has labels fixed by construction, before any system run. Seventy-five cases per subdomain. 184 hallucinated statements — 140 clearly corrupted facts plus 44 borderline, hedged-wording cases — and 116 correct control statements. Every single label traces back to one of the six reference standards, so it's independently auditable, not just one person's judgment call.

### Slide 8 — Results: 0.84 Accuracy, 0.76 Recall (7:05–8:05)

At our calibrated 40% alert threshold, across all 300 cases: 0.840 accuracy, 0.972 precision, 0.761 recall, and an F1 score of 0.854. Concretely, that's 140 of 184 hallucinations caught, with only 4 false alarms out of 116 correct statements. Mean latency in the deployed configuration is 1.26 seconds — comfortably inside our 2-second real-time target.

### Slide 9 — Every Subdomain Covered — and the Ablation (8:05–9:05)

Breaking that down by subdomain: accuracy ranges from 0.787 on electrical up to 0.880 on mechanical and safety — so no subdomain is a blind spot.

And here's the ablation that I think matters most: the rule layer alone gets 0.033 recall — essentially nothing — but *zero* false positives. The full pipeline, adding the LLM judge, jumps to 0.761 recall. That number answers a real question: is the hybrid design actually necessary, or could you get away with just the deterministic rules? The answer is no — the LLM judge is doing the large majority of the detection work, and the rule layer's job is precision, not coverage.

### Slide 10 — A Threshold Recalibration, Made Transparent (9:05–10:15)

One more thing we want to be upfront about. When we inspected the judge's score distribution, we found it concentrates single-violation detections around 45%. Our original 50% alert threshold was actually cutting into that cluster — at 50%, we'd have caught only 11 cases, for 0.060 recall. Recalibrating to 40% raised that to 140 cases and 0.761 recall.

We're reporting this openly as a diagnosed and corrected calibration effect, not hiding it behind the headline numbers — we think that kind of transparency matters as much as the accuracy figure itself. For context, our recall is lower than single-domain tools like SelfCheckGPT — but those aren't a controlled re-run on our data, and they don't attempt four subdomains simultaneously under a two-second budget.

### Slide 11 — What's Next (10:15–11:05)

We're stating our limitations plainly. Before committing to the formal evaluation, we first sanity-checked the system on real, live LLM answers to common automotive questions — every one scored below the alert threshold, with zero false positives. That early result gave us the confidence to then invest in building a properly controlled benchmark: the 300-case corpus, constructed through deliberate fault injection rather than harvested from live output, so we could fix the exact subdomain balance and label quality in advance. Labels come from a single annotator, though every one is auditable. And our knowledge base of 146 entries is a curated slice, not the full text of six standards.

Planned next steps: dense vector retrieval to resist paraphrase evasion, a fine-tuned local model to remove dependence on external APIs for OEM data-privacy needs, pluggable private knowledge bases, and extending this architecture beyond automotive — to aerospace and medical devices.

### Slide 12 — Conclusion (11:05–11:45)

To close: a deterministic rule engine stops data-driven errors in under a millisecond with zero false alarms, and a retrieval-grounded LLM judge catches the reasoning-driven errors that rules can't — drafting repairs anchored in real standards. All of it running in real time, inside the engineer's own workflow.

0.840 accuracy, 0.972 precision, 0.761 recall, 0.854 F1 — measured against an independent, standards-traced ground truth, not asserted.

Thank you — I'm happy to take your questions.

---

## Delivery & Practice Notes

- **Time yourself out loud at least twice** before the session. This script lands around 11 minutes at a natural pace — if you're consistently running past 12, cut detail from Slides 6 and 11 first (implementation detail and future work are the most compressible).
- **Slow down on the numbers** (Slides 8–10) — that's the part reviewers and the audience will actually remember. Don't rush the confusion-matrix figures.
- **Slide 9's ablation is your strongest moment** — it directly answers "why not just use rules?" Say it with confidence; it's the cleanest, most defensible result in the paper.
- Online presenters: join the Google Meet at least 10 minutes early, have both the PPTX and a PDF export ready, and mute notifications.

## Anticipated Q&A — and honest answers to have ready

- **"Why is recall only 0.76, lower than SelfCheckGPT's 91%?"** → SelfCheckGPT is measured on a single subdomain (ADAS text) with 1.5–4s latency; our number covers four subdomains at under 2 seconds, and the comparison in the paper is explicitly not a controlled re-run — it's context, not a benchmark claim.
- **"Isn't grading against your own labels circular?"** → No — ground truth is fixed by construction from the six standards *before* any system run; the system's score never feeds back into the labels.
- **"Who labeled the 300 cases?"** → Single annotator (the first author), stated as a limitation in the paper; every label is independently auditable because it reduces to a verifiable claim about a published standard. A second annotator and Cohen's κ are planned.
- **"Is this deployed in production / containerized?"** → Be accurate here: the current implementation is a single FastAPI service you can run and demo locally (extension + dashboard both work against it). If asked directly about Kubernetes/Docker orchestration, describe it as the intended production-hardening path rather than something currently running — don't claim a live cluster deployment you can't show.
- **"Can you show it live?"** → You have a working local demo (extension + dashboard) — if the session allows a quick live check, it's ready; otherwise, offer to demo after the session.
