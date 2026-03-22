# Architecture

## System Overview

Travel Language Coach presents **one coach** on the surface — a friendly,
voice-first language tutor that helps travelers practice real-world
conversations before and during a trip. Underneath, **six specialized agents**
and a speech layer collaborate to deliver each session. No single agent owns
the full pipeline; the Orchestrator coordinates handoffs so every agent
operates in its area of expertise.

```
┌──────────────────────────────────────────────────────┐
│                    User (Learner)                     │
│          Sees one coach, hears one voice              │
└────────────────────────┬─────────────────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │     Orchestrator Agent        │
         │  (session lifecycle, routing) │
         └───┬───┬───┬───┬───┬───┬──────┘
             │   │   │   │   │   │
    ┌────────┘   │   │   │   │   └────────┐
    ▼            ▼   │   ▼   ▼            ▼
 Memory     Scenario │ Phrase  Tutor   Evaluator
 Agent       Agent   │ Retrieval Agent   Agent
                     │  Agent
                     ▼
               Speech Layer
          (STT / TTS – future)
```

---

## Agent Architecture

### Full Session Flow

```
User speaks / types
       │
       ▼
┌──────────────┐
│ Orchestrator │  1. Create session, load learner context
└──────┬───────┘
       │
       ├──► Memory Agent ──────► load learner profile & history
       │
       ├──► Scenario Agent ────► select scenario (weak spots, difficulty)
       │
       ├──► Phrase Retrieval ──► load phrase pack + culture notes
       │
       ▼
┌──────────────┐
│  Tutor Agent │  2. Role-play as local persona
│              │     - opening line in target language
│              │     - respond to learner turns
│              │     - push repair before giving answers
└──────┬───────┘
       │  (loop: learner input → tutor response)
       │
       ▼
┌──────────────┐
│   Speech     │  3. (Future) STT → text, text → TTS
│   Layer      │     Currently text-based
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Evaluator   │  4. Score transcript on 7 dimensions
│   Agent      │     - extract & classify mistakes
│              │     - generate recap + next drill
└──────┬───────┘
       │
       ├──► Memory Agent ──────► record mistakes, update mastery,
       │                         append session history
       │
       ▼
┌──────────────┐
│ Orchestrator │  5. Compile final recap
│   (recap)    │     - scores, mistakes, next drill, rating
└──────────────┘
       │
       ▼
   User sees recap
```

### Agents Summary

| # | Agent             | Purpose                                        |
|---|-------------------|-------------------------------------------------|
| 1 | Orchestrator      | Session lifecycle, agent routing, recap assembly |
| 2 | Tutor             | Live role-play in target language                |
| 3 | Evaluator         | Post-session scoring, mistake extraction, recap  |
| 4 | Scenario          | Scenario selection and difficulty adjustment     |
| 5 | Memory            | Persistent storage of profiles, mistakes, mastery|
| 6 | Phrase Retrieval  | Vetted phrase packs, polite alternatives, culture|
| — | Speech Layer      | (Future) STT / TTS for voice-first interaction   |

---

## Agent Responsibilities

### 1. Orchestrator Agent

- Manages the full session lifecycle: create → route → finalize.
- Determines which agents to activate based on session mode
  (e.g., `LIVE_MISSION` engages all agents; `PHRASE_COACH` skips evaluator).
- Compiles the final recap from evaluator scores, mistakes, and drill
  recommendations.

### 2. Tutor Agent

- Role-plays as a local persona (waiter, shopkeeper, clerk) in the target
  language for the entire mission.
- Pushes the learner to self-repair before revealing correct forms (max 2
  unaided attempts).
- Adapts speech complexity to the learner's estimated level while keeping
  conversations culturally authentic.

### 3. Evaluator Agent

- Scores each session across 7 weighted dimensions (1–5 scale).
- Extracts every mistake from the transcript and classifies it by type,
  severity, and correction label.
- Generates an encouraging recap highlighting strengths plus 1–2 areas to
  improve, and recommends the single most impactful next drill.

### 4. Scenario Agent

- Maintains a registry of scenarios organized by country, category, and
  difficulty.
- Selects the best next scenario by prioritizing weak categories, avoiding
  recent repeats, and matching difficulty to performance.
- Adjusts difficulty up (score ≥ 4.0) or down (score < 2.5) after each
  session.

### 5. Memory Agent

- Persists learner profiles, couple profiles, mistake histories, and phrase
  mastery records in memory (designed for easy DB upgrade).
- Tracks mistake recurrence by matching `(learner_id, source_phrase, type)`
  to surface persistent weaknesses.
- Provides aggregated learning history (total sessions, average score,
  recurring mistakes, weak phrases).

### 6. Phrase Retrieval Agent

- Loads pre-vetted phrase packs organized by language and scenario category.
- Returns polite alternatives when the learner's phrasing is too blunt or
  informal, and simplified versions when the learner struggles.
- Supplies country- and category-specific culture notes (greetings etiquette,
  tipping customs, etc.).

---

## Data Flow

### Session Modes and Active Agents

| Mode              | Agents Activated                                          |
|-------------------|-----------------------------------------------------------|
| `LIVE_MISSION`    | Scenario → Phrase Retrieval → Tutor → Evaluator → Memory  |
| `COUPLE_MISSION`  | Scenario → Phrase Retrieval → Tutor → Evaluator → Memory  |
| `REPAIR_DRILL`    | Tutor → Phrase Retrieval → Evaluator → Memory              |
| `PHRASE_COACH`    | Memory → Phrase Retrieval → Tutor                          |
| `REVIEW`          | Memory → Phrase Retrieval → Evaluator                      |

### Data Sources

```
data/
├── scenarios/{country}/scenarios.json   ← mission templates
├── phrasepacks/{country}/phrases.json   ← vetted phrases + alternatives
└── culture/{country}.json               ← etiquette & customs
```

All static data is loaded at session start and passed to agents as context,
keeping each agent stateless with respect to the file system.

---

## Anti-Hallucination Strategy

Language correctness is critical — a coach that teaches wrong phrases is worse
than no coach. The system uses a **retrieval-first hierarchy** to minimize
model-generated language:

```
Priority 1 ─► Vetted phrase packs
              Pre-authored, human-reviewed phrases stored in
              data/phrasepacks/{country}/phrases.json.

Priority 2 ─► Scenario-specific phrases
              Phrases filtered by the current scenario's category
              and difficulty level.

Priority 3 ─► Polite alternative mappings
              Explicit informal → polite mappings stored alongside
              phrase packs (e.g., "Je veux" → "Je voudrais").

Priority 4 ─► Model-generated (constrained)
              LLM fallback for simplified versions or culture tips
              when no stored match exists. Constrained by scenario
              context and learner level.

Priority 5 ─► Free generation (avoided)
              Open-ended LLM generation is the last resort and is
              limited to conversational flow during tutoring turns.
```

Supporting mechanisms:

- **Transcript-based evaluation** — the Evaluator scores what the learner
  *actually said*, not invented examples.
- **Culture notes as ground truth** — stored facts prevent fabricated cultural
  advice.
- **Scenario-bound context** — the Tutor receives the phrase pack for the
  active scenario, narrowing the generation space.

---

## Design Principles

### 1. Voice-First

The system is designed around spoken interaction. Even in the current
text-based form, the Tutor stays in the target language, uses natural fillers,
and mirrors how a real local would speak. The architecture reserves a Speech
Layer slot for STT/TTS integration.

### 2. Retrieval-Backed Correctness

Phrases, polite alternatives, and culture notes come from curated data files
first. The LLM fills gaps but never overrides stored content. This keeps
language output trustworthy and auditable.

### 3. Memory-Driven Repetition

The Memory Agent tracks every mistake with recurrence counts. Scenarios and
drills are selected to re-expose the learner to weak areas rather than moving
on after a single correction. Spaced repetition is structural, not accidental.

### 4. Separate Live from Judgment

The Tutor never scores. The Evaluator never tutors. Splitting the live
coaching role from the post-session judgment role prevents the Tutor from
over-correcting mid-conversation and lets the Evaluator assess objectively
without conversational pressure.
