# Speech Script — Easy English Version
### "Trust, But Verify" (AIBThings 2026, Paper #465)

**Goal: 10–12 minutes of talking, then 1–3 minutes for questions. Total: 15 minutes.**
This version uses short sentences and simple words. Practice it out loud 2–3 times with a phone timer. If you go past 12 minutes, it is okay to skip the *italic* sentences marked "(optional — skip if short on time)" below.

---

### Slide 1 — Title (0:00–0:30)

Good [morning/afternoon], everyone. My name is Jaweher Hichri. My co-author is Dr. Sameh Mansour, from Grand Valley State University. Today we present our paper: "Trust, But Verify: A Hybrid RAG System for Real-Time Detection and Correction of LLM Hallucinations in Automotive Engineering."

### Slide 2 — Introduction & Motivation (0:30–1:50)

Today, car engineers often use AI language models — like GPT-4, Claude, and LLaMA. They use them to write code, to read requirements, and to check safety rules like ISO 26262.

But these AI models have a problem: they "hallucinate." This means they say something wrong, but they say it with full confidence. It sounds correct, but it is not correct. In a safety field like cars, this is dangerous. It is not just a small mistake — it can break safety rules.

These three examples come from our paper's introduction. First: the AI invents a fake signal name. The correct name, from the COVESA VSS standard, is "Vehicle-dot-Speed." Second: the AI says the brakes react in 1 millisecond. The real, tested time is 50 to 150 milliseconds. Third: the AI talks about "ASIL Z." This safety level does not exist. The ISO 26262 standard defines only A, B, C, and D.

*(optional — skip if short on time)* We use this same signal-name example again later, in Section 4, to build our 300 test cases. Other researchers, Pavel and colleagues, also found similar signal-name mistakes in AI-written code.

*(optional — skip if short on time)* The good news: many car engineering facts are fixed and written down in official documents. So we can check many AI mistakes automatically.

### Slide 3 — The Gap in Current Research (1:50–2:50)

We read 14 research papers about AI hallucination, from 2022 to 2026. We found two open problems.

Problem A: No paper tests all four important car engineering areas together — Mechanical, Electrical, Software, and Safety. Every paper looks at only one area.

Problem B: No tool exists that can detect, test, AND fix these errors in real time. One method, called SelfCheckGPT, is accurate, but slow — it takes 1.5 to 4 seconds. Another method only works with code, not with normal sentences.

### Slide 4 — What We Built (2:50–3:50)

So, we made three things. First: our research review, which shows these two problems clearly. Second: we built "The Verifier" — a real-time tool that checks AI text and fixes mistakes. It works as a Chrome extension, plus a live dashboard. Third: we built a test set of 300 cases, covering all four car engineering areas. This is the first test set of its kind for this topic.

One important point: our new idea is not a new detection method. Our contribution is that we took an existing idea about hallucination types, and we turned it into a real, working, two-part system — and we tested it honestly.

### Slide 5 — A Seven-Stage Hybrid Pipeline (3:50–5:10)

Now, how does the system work? It has seven steps.

Step 1: a fast rule-checker, with 25 fixed rules. It catches wrong signal names and wrong safety levels in less than one millisecond, and it is 100% correct on the things it checks.

Step 2: the system searches our knowledge base and finds the 5 most useful facts, in about 5 milliseconds.

Step 3: an AI judge reads the text and the facts together, decides if there is a mistake, and writes a correction. This takes 300 to 400 milliseconds.

Step 4: the system combines both answers. If Step 1 already found a clear, serious error, that answer always wins over the AI judge.

Steps 5 to 7 check the quality of the correction, save the result, and update the live dashboard.

The main idea: fast, sure rules go first. The AI judge only looks at what is left after that.

### Slide 6 — Grounded in Six Automotive Standards (5:10–6:05)

This system needs good, trusted information. We built a knowledge base with 146 facts, from six official car-industry sources. Every fact has two parts: the correct answer, and the common wrong answer. This helps the AI understand the difference clearly.

*(optional — skip if short on time)* We chose a simple, fast search method called TF-IDF — under 5 milliseconds, no powerful graphics card needed. We can also update it in minutes when a standard changes. The Chrome extension is the front door for the user. The dashboard shows live quality numbers.

### Slide 7 — Ground Truth Fixed Before Any System Run (6:05–7:05)

Now, let's talk about testing. Many papers make a common mistake: they use the system's own score to decide what is "correct," and then they use that same score to test the system. This is unfair — it is like grading your own exam with your own answer key.

We avoided this problem. We wrote the correct answers for our 300 test cases first, before running the system at all. We used 75 cases from each of the four areas. In total: 184 cases have a real mistake — 140 are clearly wrong, and 44 are written in a softer, hidden way. 116 cases are fully correct. Every single answer comes from one of our six official standards. So anyone can check our answer key.

### Slide 8 — Results: 0.84 Accuracy, 0.76 Recall (7:05–8:05)

Here are our results, using the best threshold, on all 300 cases: Accuracy is 0.840. Precision is 0.972. Recall is 0.761. F1 score is 0.854.

In simple words: the system found 140 mistakes out of 184. It made only 4 false alarms, out of 116 correct sentences. The average answer time was 1.26 seconds — well under our 2-second goal.

### Slide 9 — Every Subdomain Covered — and the Ablation (8:05–9:05)

Let's look closer at each area. Accuracy goes from 0.787 (Electrical) up to 0.880 (Mechanical and Safety). So the system works well in every area — no weak spot.

Now, an important test: what if we remove the AI judge, and keep only the simple rules? Recall drops to just 0.033 — almost nothing — though it still makes zero false alarms. Add the AI judge back, and recall jumps to 0.761. So yes, we need both parts: the AI judge finds most of the real mistakes, and the rules keep the system precise.

### Slide 10 — A Threshold Recalibration, Made Transparent (9:05–10:15)

One more honest point. We found that the AI judge often gives a score near 45% for a single mistake. Our first "alert level" was 50% — too high. At 50%, we only caught 11 cases, and recall was just 0.060.

So we changed the alert level to 40%. This one change raised our result to 140 cases caught, and recall of 0.761.

We are telling you this openly, because we want to show the real story, not just the best numbers. Yes, other tools like SelfCheckGPT show higher recall — but they only test one area, not four together, so it is not a fair, direct comparison.

### Slide 11 — What's Next (10:15–11:05)

We are honest about our limits. First, we built our test cases by hand, not from real, live AI answers. *(optional — skip if short on time)* In a small extra check, real AI answers to normal car questions were all correct, with no false alarms. Second, one person wrote all the answer labels, but every label can be checked against a public standard. Third, our knowledge base has 146 facts — a small part of the full official standards.

Our future plans: a smarter search method; our own small AI model, so we do not depend on outside companies; private rules for individual companies; and using this same idea in other safety fields, like airplanes or medical devices.

### Slide 12 — Conclusion (11:05–11:45)

To close: our fast rule system stops simple, clear mistakes in under one millisecond, with zero false alarms. Our AI judge, using real facts, catches the harder, reasoning mistakes — and writes a correct answer. All of this happens in real time, inside the engineer's normal work.

Our final numbers: 0.840 accuracy, 0.972 precision, 0.761 recall, 0.854 F1 score. These numbers come from a fair, independent test — we did not just guess them.

Thank you very much. I am happy to answer your questions.

---

## Easy tips for speaking

- **Speak slowly.** It is okay to pause after a number or a hard word.
- **Practice the hard words** before the talk: "hallucination," "automotive," "ISO 26262," "AUTOSAR," "ablation," "recalibration." Say each one 5 times alone, then in the full sentence.
- **Look at the audience**, not just the screen. You know this topic very well — trust yourself.
- **If you forget a word, keep going.** Use a simple word instead. The audience wants to understand your idea, not perfect grammar.
- **Time yourself** with a phone timer at home, 2 times, before the real day.

## Simple answers for hard questions

- **"Why is your recall only 0.76, when other tools show 90%+?"**
  → "Those tools only test one small area. We test four areas together, in under 2 seconds. It is a harder task."
- **"Is this test fair? Are you grading your own test?"**
  → "No. We wrote all correct answers first, before we ran the system. The system's score never changes the answer key."
- **"Who decided which answers are correct?"**
  → "I did, as the main author. But every answer comes from a public, official standard. Anyone can check it. Adding a second person to check is our next planned step."
- **"Do you have it running on Docker or Kubernetes, like in the paper?"**
  → "Right now, the working version runs as one simple service — you can see it working live. Docker and Kubernetes are part of our future production plan, not running today."
- **"Can we see it working live?"**
  → "Yes! The Chrome extension and dashboard both work. I am happy to show it after this session."
