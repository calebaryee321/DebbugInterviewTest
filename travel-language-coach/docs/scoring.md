# Scoring System

## Overview

Every session is scored across **7 dimensions** on a 1–5 scale. A weighted
average produces a single composite score that drives difficulty adjustment,
scenario selection, and learner profile updates.

---

## Scoring Dimensions

| #  | Dimension                | Weight | Description                                                                 |
|----|--------------------------|--------|-----------------------------------------------------------------------------|
| 1  | **Comprehensibility**    | 0.20   | Could a native speaker understand the learner? Clarity of communication.    |
| 2  | **Task Completion**      | 0.20   | Did the learner achieve the mission goal (order food, get directions, etc.)?|
| 3  | **Recovery**             | 0.15   | How well did the learner self-correct or recover when they made a mistake?  |
| 4  | **Confidence/Hesitation**| 0.15   | Did the learner speak with confidence, or hesitate and stall frequently?    |
| 5  | **Grammar**              | 0.10   | Grammatical accuracy of the learner's utterances.                           |
| 6  | **Naturalness**          | 0.10   | Does the speech sound native-like? Appropriate idioms, fillers, flow.       |
| 7  | **Politeness/Register**  | 0.10   | Did the learner use the right level of formality for the situation?         |

### Why These Weights?

Communication-heavy dimensions (**comprehensibility**, **task completion**)
carry the most weight because the system prioritizes *getting the message
across* in a real travel scenario. **Recovery** and **confidence** are weighted
next because they reflect resilience under pressure — a key skill for
travelers. Traditional accuracy metrics (**grammar**, **naturalness**,
**register**) matter but are secondary to successful communication.

---

## Weight Distribution

```
comprehensibility      ████████████████████  20%
task_completion        ████████████████████  20%
recovery               ███████████████       15%
confidence_hesitation  ███████████████       15%
grammar                ██████████            10%
naturalness            ██████████            10%
politeness_register    ██████████            10%
                                      Total 100%
```

---

## Rating Scale

Each dimension is scored on a 1–5 integer/float scale:

| Score | Label | Meaning                                                    |
|-------|-------|------------------------------------------------------------|
| 1     | Poor  | Significant difficulty; communication largely fails        |
| 2     | Weak  | Partial success but major gaps remain                      |
| 3     | OK    | Gets the point across with noticeable errors               |
| 4     | Good  | Clear and mostly natural with minor issues                 |
| 5     | Great | Near-native performance; confident and accurate            |

---

## Weighted Average Formula

```python
weighted_average = (
    comprehensibility     * 0.20
  + task_completion       * 0.20
  + recovery              * 0.15
  + confidence_hesitation * 0.15
  + grammar               * 0.10
  + naturalness           * 0.10
  + politeness_register   * 0.10
)
```

The result is a single float in the range **1.0 – 5.0**.

### Example

| Dimension              | Score | × Weight | Contribution |
|------------------------|-------|----------|--------------|
| Comprehensibility      | 4.0   | × 0.20   | 0.80         |
| Task Completion        | 3.0   | × 0.20   | 0.60         |
| Recovery               | 3.5   | × 0.15   | 0.525        |
| Confidence/Hesitation  | 2.5   | × 0.15   | 0.375        |
| Grammar                | 3.0   | × 0.10   | 0.30         |
| Naturalness            | 2.0   | × 0.10   | 0.20         |
| Politeness/Register    | 4.0   | × 0.10   | 0.40         |
| **Weighted Average**   |       |          | **3.20**     |

Rating: **Functional**

---

## Rating Thresholds

| Weighted Average   | Rating            |
|--------------------|-------------------|
| 1.0 – 1.99        | Needs Practice    |
| 2.0 – 2.99        | Developing        |
| 3.0 – 3.99        | Functional        |
| 4.0 – 5.0         | Strong            |

---

## How Scoring Drives Adaptation

### Difficulty Adjustment

After each session the Scenario Agent checks the weighted average:

| Condition               | Action                                    |
|-------------------------|-------------------------------------------|
| Weighted average ≥ 4.0  | **Increase** difficulty one level         |
| Weighted average < 2.5  | **Decrease** difficulty one level         |
| 2.5 ≤ average < 4.0     | **Stay** at current difficulty            |

Difficulty levels progress through:
`BEGINNER → ELEMENTARY → INTERMEDIATE → UPPER_INTERMEDIATE → ADVANCED`

### Trend Analysis

The Scoring Engine compares the mean of the first half of recent scores
against the mean of the second half:

| Delta        | Trend Label |
|--------------|-------------|
| > +0.25      | Improving   |
| < −0.25      | Declining   |
| −0.25 to +0.25 | Stable   |

Trends are surfaced in recaps so learners can see momentum.

---

## How Scores Feed Into Memory and Scenario Selection

```
Session ends
     │
     ▼
Evaluator scores transcript ──► ScoreBreakdown (7 dimensions)
     │
     ├──► Scoring Engine
     │       • Computes weighted average
     │       • Determines rating label
     │       • Identifies weakest & strongest dimensions
     │
     ├──► Memory Agent
     │       • Appends session summary (score, mistakes) to history
     │       • Updates mistake recurrence counts
     │       • Feeds into get_history() aggregations
     │
     └──► Scenario Agent (next session)
             • Reads weak_scenarios from learner profile
             • Reads recent session history to avoid repeats
             • Uses score to adjust difficulty level
             • Selects scenario targeting weakest areas
```

### Feedback Loop

1. Low scores on **politeness_register** → Memory records `register` mistakes
   → Scenario Agent prioritizes scenarios with formal interactions
   (e.g., hotel check-in) → Phrase Retrieval loads polite alternatives.

2. High scores across the board (≥ 4.0) → difficulty increases →
   pressure elements intensify (faster speech, impatient locals in future
   phases).

3. Recurring mistakes (high `recurrence_count`) are surfaced in recaps and
   used by the Evaluator when recommending the next drill.
