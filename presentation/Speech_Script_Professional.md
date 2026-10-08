# Speech Script — Professional, Clear English
### "Trust, But Verify" (AIBThings 2026, Paper #465)

**Target: 10–12 minutes of presentation, then 1–3 minutes for questions. Total: 15 minutes.**
This version keeps a formal, academic tone while using clear, moderate-length sentences that are easy to deliver aloud. Practice it 2–3 times with a timer. Sentences marked *(optional)* can be cut if you are short on time, without breaking the flow.

---

### Slide 1 — Title (0:00–0:30)

Good [morning/afternoon], everyone. I am Jaweher Hichri, presenting joint work with my co-author, Dr. Sameh Mansour, from Grand Valley State University. Our paper is titled "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:30–1:50)

Automotive engineers increasingly rely on large language models — GPT-4, Claude, LLaMA — to draft code, interpret requirements, and support compliance with standards such as ISO 26262.

The difficulty is that these models hallucinate: they produce fluent, confident output that is factually incorrect. In a safety-critical domain, this is not a minor inconvenience — it directly threatens compliance and safety.

Consider three concrete examples, drawn directly from our paper's introduction. A model may invent a signal path such as "Vehicle-dot-Motor-dot-Velocity," when the correct specification — per COVESA VSS 4.0 — is "Vehicle-dot-Speed." It may state that anti-lock braking responds within one millisecond, when the validated range encoded in our knowledge base is fifty to one hundred fifty milliseconds. Or it may reference "ASIL Z," a safety level that does not exist — ISO 26262:2018 defines only A, B, C, and D.

*(optional)* This same corrupted signal path recurs in Section IV, where it illustrates the construction of our 300-case evaluation corpus; comparable VSS-related hallucinations in automotive code generation have also been documented by Pavel et al.

*(optional)* This domain offers a structural advantage: many of its critical facts are finite and formally defined, which means a substantial share of these errors can be verified deterministically, against a published standard, rather than judged only for plausibility.

### Slide 3 — The Gap in Current Research (1:50–2:50)

We conducted a review of fourteen papers on LLM hallucination published between 2022 and 2026, and identified two open gaps.

The first, which we call the Subdomain Gap: no existing benchmark evaluates hallucinations across all four critical automotive subdomains — mechanical, electrical, software, and safety — simultaneously. Each prior study addresses a single subdomain in isolation.

The second, the Usability Gap: no deployable, real-time tool both detects and corrects these errors. SelfCheckGPT achieves strong recall but requires 1.5 to 4 seconds per query, which is too slow for interactive use. AST-based parsing is fast and precise, but limited strictly to source code.

### Slide 4 — What We Built (2:50–3:50)

In response, we developed three contributions. First, this structured literature review, which makes both gaps explicit. Second, The Verifier: an end-to-end, real-time pipeline — delivered as a Chrome extension with a live Streamlit dashboard — that integrates directly into the engineer's existing workflow. Third, a 300-case evaluation corpus spanning all four subdomains: to our knowledge, the first cross-subdomain, standards-traced benchmark of its kind in this literature.

I want to state our contribution precisely: this is not a new detection algorithm. It is a deployable mapping of an established causal hallucination taxonomy onto a working, two-layer architecture, together with a rigorous methodology to evaluate it.

### Slide 5 — A Seven-Stage Hybrid Pipeline (3:50–5:10)

The system processes each request through a seven-stage pipeline.

Stage one is a deterministic pattern layer: twenty-five fixed rules and seven context-aware checks that identify invalid signal paths and impossible safety levels in under one millisecond, achieving one hundred percent precision on that rule set.

Stage two retrieves the five most relevant knowledge-base entries using TF-IDF similarity, in approximately five milliseconds. Stage three is an LLM judge, served on Groq, which evaluates the input against that retrieved context and drafts a grounded correction within three hundred to four hundred milliseconds.

Stage four performs decision fusion: when stage one identifies a critical, deterministic violation, that verdict always takes precedence over the model's judgment. Stages five through seven handle correction quality, persistence, and live dashboard metrics.

The governing principle is straightforward: deterministic rules are evaluated first and trusted fully; the probabilistic judge addresses only what remains.

### Slide 6 — Grounded in Six Automotive Standards (5:10–6:05)

This architecture depends on a reliable knowledge base. We curated one hundred forty-six entries from six authoritative sources, including COVESA VSS, ISO 26262, SOTIF, SAE J1979, and AUTOSAR. Each entry is bidirectional, pairing the correct fact with its common hallucinated variant, which removes ambiguity for the model.

*(optional)* We selected TF-IDF over dense embeddings deliberately: it requires no GPU, maintains sub-five-millisecond latency, and allows the index to be rebuilt within minutes whenever a standard is updated.

### Slide 7 — Ground Truth Fixed Before Any System Run (6:05–7:05)

I want to turn to our evaluation methodology, which we consider central to this work. A common weakness in this literature is using a system's own score both to define ground truth and to measure performance — which effectively grades the system against itself.

To eliminate that circularity, our labels were fixed by construction, before any system run. The corpus contains 300 cases, seventy-five per subdomain: 184 hallucinated statements — 140 clearly corrupted facts and 44 borderline, hedged variants — alongside 116 correct control statements. Every label traces to one of our six reference standards, making the evaluation independently auditable rather than dependent on a single reviewer's judgment.

### Slide 8 — Results (7:05–8:05)

At our calibrated forty-percent alert threshold, across all 300 cases, the system achieves an accuracy of 0.840, a precision of 0.972, a recall of 0.761, and an F1 score of 0.854. In concrete terms, it correctly identifies 140 of 184 hallucinations, with only four false alarms among 116 correct statements. Mean latency in the deployed configuration is 1.26 seconds, comfortably within our two-second real-time target.

### Slide 9 — Per-Subdomain Results and Ablation (8:05–9:05)

Performance is consistent across subdomains, with accuracy ranging from 0.787 on electrical to 0.880 on mechanical and safety — indicating no significant blind spot.

Our ablation study addresses a direct question: is the hybrid design necessary? Using the rule layer alone yields only 0.033 recall, though with zero false positives. Adding the LLM judge raises recall to 0.761. This confirms that the language model provides the majority of detection coverage, while the rule layer's role is to preserve precision.

### Slide 10 — A Threshold Recalibration, Reported Transparently (9:05–10:15)

One further finding deserves mention. On inspection, the judge's scoring consistently concentrated single-violation detections around forty-five percent. Our original fifty-percent alert threshold therefore missed a substantial share of true positives, catching only eleven cases, for a recall of 0.060. Recalibrating to forty percent raised that figure to 140 cases and a recall of 0.761.

We report this openly as a diagnosed and corrected calibration effect, rather than presenting only the favorable outcome. For context, our recall is lower than single-domain tools such as SelfCheckGPT; however, that comparison is not a controlled re-run on identical data, and those tools do not address four subdomains under a two-second latency constraint.

### Slide 11 — Limitations and Future Work (10:15–11:05)

We state our limitations plainly. The corpus was constructed through deliberate fault injection rather than harvested from live model output. *(optional)* In a supplementary check, however, real model responses to common automotive queries were consistently correct and scored below the alert threshold. Labeling was performed by a single annotator, though every label is independently auditable against a published standard. Our knowledge base of 146 entries represents a curated subset, not the full text of six standards.

Planned extensions include dense vector retrieval for improved resistance to paraphrase evasion, a fine-tuned local model to remove dependence on external APIs, support for private, pluggable knowledge bases, and generalization of this architecture to other safety-critical domains such as aerospace and medical devices.

### Slide 12 — Conclusion (11:05–11:45)

In summary: a deterministic rule engine neutralizes data-driven errors in under one millisecond with zero false alarms, while a retrieval-grounded language model judge addresses reasoning-driven errors and drafts standards-backed corrections — all operating in real time, within the engineer's existing workflow.

Evaluated against an independent, standards-traced ground truth, The Verifier achieves 0.840 accuracy, 0.972 precision, 0.761 recall, and an F1 score of 0.854.

Thank you for your attention. I welcome your questions.

---

## Delivery Notes

- **Maintain a measured pace.** A brief pause after each metric (accuracy, precision, recall, F1) gives the audience time to absorb the number.
- **Rehearse the technical terms** in advance — hallucination, automotive, AUTOSAR, ablation, recalibration — so they are delivered smoothly rather than read.
- **Slide 9 is your strongest result.** The ablation directly answers "why not use rules alone?" — deliver it with confidence.
- **If a word is momentarily forgotten, continue with a simpler equivalent** rather than pausing; clarity matters more than exact phrasing.
- **Time the full script** at least twice beforehand. If consistently over twelve minutes, cut the sentences marked *(optional)* first.

## Prepared Responses for Likely Questions

- **"Why is recall only 0.76, when SelfCheckGPT reports over 90%?"**
  → "SelfCheckGPT is evaluated on a single subdomain with 1.5 to 4 seconds of latency per query. Our result covers four subdomains simultaneously, under two seconds — a substantially harder task, and the comparison is contextual rather than a controlled benchmark."
- **"Is this evaluation circular — are you grading the system against itself?"**
  → "No. Ground truth was fixed by construction, before any system run, and is never derived from the system's own score."
- **"Who assigned the ground-truth labels?"**
  → "A single annotator, the first author — stated explicitly as a limitation. Every label is independently verifiable against a published standard. Adding a second annotator and reporting inter-rater agreement is planned."
- **"Is the system currently containerized or deployed on Kubernetes, as described in the paper?"**
  → "The current implementation runs as a single service, which I can demonstrate live. Containerized, high-availability deployment is part of our planned production hardening, not the present configuration."
- **"Could you demonstrate the system live?"**
  → "Yes — the Chrome extension and dashboard are both functional. I would be glad to demonstrate them following this session."
