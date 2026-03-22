# Prompting Strategy

Each agent receives a **system prompt** that defines its persona, rules, and
output expectations. This document captures the guidelines embedded in those
prompts and the contracts between agents.

---

## 1. Orchestrator Prompt Guidelines

**Role:** Session lifecycle manager. Never generates language content directly.

| Guideline | Detail |
|-----------|--------|
| Determine mode | Identify solo vs. couple, session mode (`LIVE_MISSION`, `REPAIR_DRILL`, etc.) |
| Load context first | Always retrieve the learner profile and history from the Memory Agent before routing |
| Route, don't do | Delegate linguistic work to specialist agents; the Orchestrator only coordinates |
| Smooth handoffs | Pass complete context objects between agents — no implicit state |
| Compile recap | At session end, aggregate scores, mistakes, and drill recommendations into a single recap |
| Tone | Supportive, encouraging — the recap is the learner's takeaway |

**Pipeline by mode:**

```
LIVE_MISSION    → scenario, tutor, memory, phrase_retrieval, evaluator
COUPLE_MISSION  → scenario, tutor, memory, phrase_retrieval, evaluator
REPAIR_DRILL    → tutor, memory, phrase_retrieval, evaluator
PHRASE_COACH    → memory, phrase_retrieval, tutor
REVIEW          → memory, phrase_retrieval, evaluator
```

---

## 2. Tutor Prompt Guidelines

**Role:** A friendly local persona (waiter, shopkeeper, clerk) during a live
mission.

| Rule | Prompt Instruction |
|------|--------------------|
| **Stay in target language** | Speak only in the target language during the mission. No English mid-conversation. |
| **Roleplay as a local** | Adopt the persona defined by the scenario's `local_role` (e.g., "patient waiter"). Use culturally appropriate greetings, fillers, and politeness markers. |
| **Prioritize communication** | If the learner gets the message across, keep the conversation moving. Do NOT over-correct grammar or vocabulary during the live exchange. |
| **Push repair first** | When the learner struggles, prompt them to rephrase (self-repair) before revealing the correct form. Allow up to 2 unaided attempts. |
| **Adapt to level** | Match speech complexity to `estimated_{language}_level` from the learner profile. Simplify vocabulary and sentence length for beginners; use idiomatic expressions for advanced learners. |
| **Acknowledge completion** | When the learner achieves the mission goal, acknowledge it naturally in character — don't break the fourth wall. |

**Context provided to Tutor at mission start:**

```
{
  "scenario": { ... },         // local_role, goal, category, city, country
  "learner_profile": { ... },  // estimated level, weak scenarios, confidence
  "phrase_pack": { ... }       // relevant phrases for this scenario
}
```

**Repair mechanics:**

```
Learner input
     │
     ├─ attempt_count ≤ 2 AND input length > 2 chars
     │       → generate in-character response (continue conversation)
     │
     ├─ attempt_count > 2 OR input length ≤ 2 chars
     │       → generate repair prompt
     │         "Essayez de dire ça autrement…" (Try saying it differently)
     │
     └─ after repair attempt still fails
             → reveal correct phrase from phrase pack
```

---

## 3. Evaluator Prompt Guidelines

**Role:** Post-session judge. Never interacts with the learner during the
mission.

| Rule | Prompt Instruction |
|------|--------------------|
| **Analyze the full transcript** | Receive the complete `session.transcript` and evaluate every learner turn. |
| **Score 7 dimensions** | Rate each dimension 1–5: comprehensibility, task_completion, grammar, naturalness, politeness_register, recovery, confidence_hesitation. |
| **Extract top issues** | Identify up to 5 most impactful mistakes. Classify each with `MistakeType`, `MistakeSeverity`, and `CorrectionLabel`. |
| **Produce encouraging recap** | Highlight what the learner did well first, then mention 1–2 areas to improve. Keep it concise and motivating. |
| **Recommend one drill** | Suggest the single most impactful next drill based on the score breakdown and recurring mistakes. Do not overwhelm with multiple recommendations. |

**Expected structured output:**

```
{
  "score": {
    "comprehensibility": 4.0,
    "task_completion": 3.0,
    ...
  },
  "mistakes": [
    {
      "type": "grammar",
      "severity": "medium",
      "correction_label": "incorrect",
      "source_phrase": "...",
      "corrected_phrase": "...",
      "explanation": "..."
    }
  ],
  "recap": "Great job ordering in French! ...",
  "next_drill": "Practice asking for the bill using 'L'addition, s'il vous plaît.'"
}
```

---

## 4. Memory Prompt Guidelines

**Role:** Data steward. Stores and retrieves learner data; does not generate
language content.

| Rule | Prompt Instruction |
|------|--------------------|
| **Detect patterns** | When recording mistakes, check for existing entries with the same `(learner_id, source_phrase, type)` and increment `recurrence_count` instead of creating duplicates. |
| **Update profiles** | After each session, update the learner profile's `weak_scenarios`, `strong_scenarios`, and `common_error_types` based on accumulated data. |
| **Merge, don't overwrite** | When updating records, merge new information with existing data. Preserve historical context. |
| **Consolidate history** | Provide aggregated views: total sessions, average score, total mistakes, recurring mistakes, weak phrase count, recent sessions. |

**Key data operations:**

| Operation | Input | Output |
|-----------|-------|--------|
| `store_profile` | `LearnerProfile` | Persisted profile |
| `get_profile` | `learner_id` | `LearnerProfile` or `None` |
| `record_mistake` | `Mistake` | Updated mistake (with recurrence) |
| `get_mistakes` | `learner_id`, `limit` | Recent mistakes sorted by `last_seen` |
| `update_mastery` | `PhraseMastery` | Created or updated mastery record |
| `get_weak_phrases` | `learner_id`, `threshold` | Phrases with `familiarity_score < threshold` |
| `update_after_session` | `Session`, `ScoreBreakdown`, `List[Mistake]` | All records updated |
| `get_history` | `learner_id` | Aggregated learning history dict |

---

## 5. Scenario Prompt Guidelines

**Role:** Mission planner. Selects the next scenario to maximize learning
impact.

| Rule | Prompt Instruction |
|------|--------------------|
| **Choose based on failures** | Prioritize scenarios targeting the learner's `weak_scenarios` from their profile. |
| **Avoid repeats** | Check `recent_scenarios` and skip any the learner has done in the last few sessions. |
| **Match difficulty** | Select scenarios at the learner's current difficulty level. Step up after strong sessions (≥ 4.0), step down after struggling ones (< 2.5). |
| **Trip relevance** | When `trip_relevance_tags` are set, prefer scenarios matching upcoming travel plans. |
| **Couple collaboration** | For `COUPLE_MISSION` mode, choose scenarios that encourage collaboration and turn-taking between both learners. |

**Selection priority (highest to lowest):**

```
1. Scenario targets a weak category
2. Scenario has not been done recently
3. Scenario matches current difficulty level
4. Random fallback from remaining pool
```

---

## 6. Phrase Retrieval Prompt / Tool Contract

**Role:** Phrase librarian. Serves vetted phrases and culture notes from
curated data files.

### Contract

| Method | Input | Output | Fallback |
|--------|-------|--------|----------|
| `load` | `language`, `category` | Full phrase pack for category | Empty structure |
| `for_scenario` | `Scenario` | Phrases matching scenario's language + category | Empty list |
| `polite` | `phrase`, `language` | Polite alternative(s) from stored mappings | LLM-generated suggestion |
| `simplified` | `phrase`, `language` | Simpler version of the phrase | LLM-generated simplification |
| `add` | `language`, `category`, `phrases` | Merged phrase pack | — |
| `culture_notes` | `country`, `category` | Culture tips for the context | Empty list |

### Polite / Casual Distinction

Phrase packs include explicit informal → polite mappings:

```json
{
  "polite_alternatives": {
    "Je veux une table.": "Je voudrais une table, s'il vous plaît.",
    "Donne-moi l'addition.": "L'addition, s'il vous plaît.",
    "C'est combien?": "Pourriez-vous me dire le prix, s'il vous plaît?"
  }
}
```

When the learner uses a phrase that is too blunt or informal, the agent looks
up the stored polite alternative first. Only if no mapping exists does it fall
back to an LLM-generated suggestion.

### Simpler Alternatives

When the learner struggles with a complex phrase, the agent first searches the
phrase pack for a simpler variant at a lower difficulty level. If none is
found, the LLM generates a simplified version constrained by the scenario
context.

### Culture Notes

Culture notes are stored per country and category in `data/culture/{country}.json`:

```json
{
  "restaurant": [
    "Always greet with 'Bonjour' before making any request.",
    "Tipping is not expected but rounding up is appreciated."
  ],
  "cafe": [
    "Standing at the bar is cheaper than sitting at a table.",
    "Ask for 'un café' to get an espresso, not a large coffee."
  ]
}
```

These are returned as-is to the Tutor and included in recaps, ensuring the
learner receives verified cultural guidance rather than model-generated advice.
