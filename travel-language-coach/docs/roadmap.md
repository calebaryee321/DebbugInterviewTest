# Build Roadmap

## Status Key

| Symbol | Meaning            |
|--------|--------------------|
| ✅     | Complete           |
| 🔧     | Partially complete |
| ⬚      | Not started        |

---

## Phase 1 — Foundation (Weeks 1–2) 🔧

> **Goal:** Repository skeleton, auth stubs, core data models, storage layer,
> and a minimal frontend shell.

| Deliverable                          | Status |
|--------------------------------------|--------|
| Repository structure & CI scaffold   | ✅     |
| Pydantic data models & enums         | ✅     |
| Agent base class & registry          | ✅     |
| All 6 agent implementations          | ✅     |
| Scoring engine & weight config       | ✅     |
| Scenario & phrase-pack JSON data     | ✅     |
| Culture notes JSON data              | ✅     |
| Session manager & learner loop       | ✅     |
| Authentication / user management     | ⬚     |
| Database persistence (replace in-memory) | ⬚ |
| Frontend shell (React / mobile)      | ⬚     |

---

## Phase 2 — Voice MVP (Weeks 3–4) ⬚

> **Goal:** A learner can run a live voice mission end-to-end — speak into the
> app, converse with the Tutor, and see a summary.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| STT integration (Whisper / Deepgram)           | ⬚     |
| TTS integration (ElevenLabs / Azure)           | ⬚     |
| Live voice mission flow (mic → STT → Tutor → TTS → speaker) | ⬚ |
| Transcript capture & storage                   | ⬚     |
| Basic role-play conversation loop              | ⬚     |
| Post-mission summary screen                    | ⬚     |

---

## Phase 3 — Evaluation Layer (Weeks 5–6) ⬚

> **Goal:** After each session the Evaluator agent scores the transcript,
> extracts mistakes, and delivers a structured recap.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| Evaluator LLM pipeline (prompt → structured output) | ⬚ |
| 7-dimension ScoreBreakdown generation          | ⬚     |
| Mistake extraction & classification            | ⬚     |
| Correction label assignment                    | ⬚     |
| Encouraging recap generation                   | ⬚     |
| Next-drill recommendation engine               | ⬚     |
| Review / recap UI screen                       | ⬚     |

---

## Phase 4 — Memory Layer (Weeks 7–8) ⬚

> **Goal:** Persistent memory across sessions — mistakes accumulate, phrase
> mastery updates, and the system adapts over time.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| Database-backed learner profile storage        | ⬚     |
| Mistake recurrence tracking & merging          | ⬚     |
| Phrase mastery score updates after each session| ⬚     |
| Weak-phrase surfacing (familiarity < threshold)| ⬚     |
| Session history aggregation                    | ⬚     |
| Adaptive scenario selection based on memory    | ⬚     |
| Trend analysis (improving / stable / declining)| ⬚     |

---

## Phase 5 — Agent Separation & Hardening (Weeks 9–10) ⬚

> **Goal:** Each agent runs behind a dedicated prompt with clear input/output
> contracts. The Orchestrator routes without leaking context between agents.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| Dedicated system prompts per agent             | ⬚     |
| Orchestrator routing logic (mode → agent list) | ⬚     |
| Input/output schema validation per agent       | ⬚     |
| Agent error handling & fallback paths          | ⬚     |
| Observability: log every agent call & latency  | ⬚     |
| End-to-end integration tests                   | ⬚     |

---

## Phase 6 — Couple Mode (Weeks 11–12) ⬚

> **Goal:** Two learners can practice together in a shared mission with
> turn-taking, handoff tracking, and joint scoring.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| CoupleProfile CRUD & linking                   | ⬚     |
| Couple mission UX (shared screen / split view) | ⬚     |
| Turn-taking / handoff event tracking           | ⬚     |
| Joint scoring (combined + individual breakdown)| ⬚     |
| Shared weakness / strength detection           | ⬚     |
| Couple-specific recap & drill recommendation   | ⬚     |

---

## Phase 7 — Retrieval Hardening (Months 4–5) ⬚

> **Goal:** Expand vetted phrase packs, add retrieval constraints, and reduce
> reliance on model-generated language.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| Expanded vetted phrase packs (5+ countries)    | ⬚     |
| Polite / casual distinction enforcement        | ⬚     |
| Simpler-alternative lookup before LLM fallback | ⬚     |
| Culture notes expansion & review pipeline      | ⬚     |
| Retrieval audit: flag any model-generated phrase served to learner | ⬚ |
| Phrase pack contribution tooling (add / review / approve) | ⬚ |

---

## Phase 8 — Realism Tuning (Months 6–8) ⬚

> **Goal:** Make practice scenarios feel closer to real travel — impatient
> locals, fast speech, regional variants, and a pre-trip simulation mode.

| Deliverable                                    | Status |
|------------------------------------------------|--------|
| Impatient / rushed local personas              | ⬚     |
| Adjustable speech speed (TTS rate control)     | ⬚     |
| City & regional dialect variants               | ⬚     |
| Background noise / ambient audio layers        | ⬚     |
| Pre-trip simulator (trip itinerary → scenario sequence) | ⬚ |
| Post-trip review mode (what went well / what to revisit)| ⬚ |
