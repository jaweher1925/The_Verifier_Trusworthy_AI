# Speech Script — Easy & Professional (Short Version)
### "Trust, But Verify" (AIBThings 2026, Paper #465)

**Target: 10 minutes of talking, then 2–5 minutes for questions. Total: 15 minutes.**
This version uses short sentences and simple, everyday English — easy to say out loud, still formal enough for a conference. At a calm pace (about 95 words per minute) plus short pauses between the 13 slides, the spoken text below takes about 11:27. Practice once with a timer to check.

---

### Slide 1 — Title (0:00–0:28)

Good [morning/afternoon], everyone. I am Jaweher Hichri. I am presenting joint work with my co-author, Dr. Sameh Mansour, from Grand Valley State University. Our paper is called "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:32–1:59)

Automotive engineers use large language models more and more. They use them to write code, understand requirements, and check standards like ISO 26262.

But these models can make mistakes. They can hallucinate — they give confident, clear answers that are simply wrong. They do not sound unsure when they are wrong. In a safety-critical field, this is a real problem.

Here are three examples. A model may invent a signal path — this is a mistake type that Pavel et al. found in their study. The correct path, from COVESA VSS, is "Vehicle-dot-Speed." A model may also give the wrong response time for a braking system. Or it may talk about "ASIL Z," a level that does not exist — ISO 26262 only has levels A to D. Each example sounds right, but each one is wrong.

### Slide 3 — The Gap in Current Research (2:03–3:11)

To find where our work fits, we read fourteen papers on LLM hallucination, from 2022 to 2026. This review also shows why our idea makes sense: other studies show that hybrid systems like ours — combining a knowledge base with a language model — can lower hallucination errors by 35 to 60 percent.

We also found two gaps. First, no study tests all four car-engineering areas together — mechanical, electrical, software, and safety. Each past study looks at only one. Second, no real-time tool both finds and fixes these errors — other methods are too slow, or they only work on code. These two gaps guided our work.

### Slide 4 — What We Built (3:15–4:09)

To close these gaps, we built three things. First, the review itself, which makes the two gaps clear. Second, **The Verifier**: a real-time tool that finds and fixes errors, delivered as a Chrome extension with a live dashboard, so it fits into normal engineering work. Third, a **300-case test set** — the first one to cover all four areas at once.

To be clear: our idea is not a new detection method. It is a working system, built on a known hallucination model, and tested carefully.

### Slide 5 — A Seven-Stage Pipeline (4:13–5:37)

Each request moves through seven quick steps, shown on screen.

Step one is a rule check: it scans the text against known wrong facts, in under one millisecond, with full accuracy. Step two, the system searches our knowledge base and pulls out the five facts that match best. Step three, if the rules found nothing, a language model reads those facts and checks the text — this takes about a third to half a second. Step four combines both results: if the rule check already found a mistake, its answer always wins over the language model's answer. Step five scores how well the fix matches our sources, to confirm it is grounded. Steps six and seven save the result and update the live dashboard, so an engineer can see it right away.

### Slide 6 — Grounded in Six Automotive Standards (5:41–6:13)

None of this works without good facts behind it. Our knowledge base has 146 checked facts, from six standards, including COVESA VSS, ISO 26262, and AUTOSAR. Each entry pairs the correct fact with its common wrong version. This keeps the system fast to check, and easy to update when standards change.

### Slide 7 — A Fair Evaluation (6:17–7:10)

How we test the system matters as much as the results. A common problem in this field is using a system's own score to both decide what is correct and to grade performance — that just grades the system against itself.

We avoided this. All 300 test labels were set before we ran the system, using the six standards, never based on the system's own output. The test set is balanced: 184 wrong cases and 116 correct ones, spread evenly across all four areas.

### Slide 8 — Results (7:14–7:53)

At our chosen alert level, across all 300 cases, the system reaches 0.840 accuracy, 0.972 precision, 0.761 recall, and an F1 score of 0.854. In simple terms, it correctly finds 140 of 184 wrong cases, with only four false alarms out of 116 correct ones. The average response time is 1.26 seconds — well within our two-second goal for real-time use.

### Slide 9 — Consistent Across Subdomains (7:57–8:34)

Accuracy stays strong across all four areas, from 0.787 to 0.880 — there is no clear weak spot. A follow-up test also shows why both layers matter: the rule layer alone gets only 0.033 recall, while the full system gets 0.761. So the language model does most of the detection work, and the rules mainly keep the system precise.

### Slide 10 — An Honest Calibration Finding & Limitations (8:38–9:50)

One finding is worth sharing directly. Our first alert level was set too strict, so it caught only eleven cases. We lowered it, based on how the model actually scores things, and detection rose to 140 cases. We share this openly, as a clear, fixed limitation — not just the final good number.

We also see clear limits. The test cases were built by us, not collected from real live use. And one person did the labeling, though every label can be checked against a public standard. Looking ahead, our next steps include better search methods, a model that runs locally for privacy, and using this same idea in other safety-critical fields beyond cars.

### Slide 11 — How The Verifier Compares (9:54–10:45)

We also compared The Verifier to three other tools: SelfCheckGPT, a code-checker called AST validation, and plain RAG. Only ours catches both kinds of error, gives a checked fix, answers in under two seconds, and is built just for cars. Our recall, 0.76, is lower than SelfCheckGPT's 0.91 — but that number is from one small area, at a slower speed, an easier task. These are separate tests, not one shared test on our data; that shared test is planned next.

### Slide 12 — Conclusion (10:49–11:16)

In short: a fast rule layer stops clear, well-known errors right away, and a grounded language model catches the harder, reasoning-based ones — both working inside the engineer's normal workflow, and measured against an independent, standards-based test rather than the system's own judgment.

### Slide 13 — Q&A (11:20–11:27)

Thank you very much for your attention. I welcome your questions.

---

## Delivery Notes

- This script keeps technical detail light — the slides carry the exact numbers, so you don't need to remember every figure by heart.
- If your practice run comes in under 10 minutes, that's fine — speak a little slower and pause a bit longer, instead of adding more words.
- Pause briefly after each of the four numbers on Slide 8 (accuracy, precision, recall, F1) — give people time to take them in.
- Slide 5 now names all seven steps — point to the diagram as you speak so the audience can follow along on screen.
- If a question asks for more detail than the slides show (for example, the exact rule count, or the Groq/LLaMA model names), a short answer is fine — offer to share the paper afterward.

## Prepared Answers for Likely Questions

- **"Why is recall only 0.76?"** → "Tools like SelfCheckGPT report higher recall, but only on one subdomain, with much higher latency. Ours covers four subdomains, under two seconds — a harder task."
- **"Is the evaluation circular?"** → "No — all labels were set before we ran the system, using the six reference standards, not the system's own score."
- **"Who labeled the test cases?"** → "One person, the first author — this is stated as a limitation. Every label can be checked against a published standard; a second reviewer is planned."
- **"Is it running on Docker or Kubernetes?"** → "The current version runs as a single service, which I can demonstrate. Full production deployment is planned future work, not the current setup."
- **"What score did ROUGE-L get?"** → "ROUGE-L is a real, used part of the system — it's step five, a live check that compares each fix to the source fact, to confirm the fix is grounded. What we don't have is one overall number for it in this paper's results — those results (accuracy, precision, recall, F1) come from a different check, comparing the system's alerts to our 300 labeled cases. We picked ROUGE-L because it's fast; the other options were too slow or checked against the wrong kind of source. Turning ROUGE-L into one overall score is a good next step."
- **"Can you show it live?"** → "Yes — happy to demonstrate the extension and dashboard after this session."
