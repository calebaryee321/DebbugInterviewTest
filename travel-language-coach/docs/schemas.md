# Data Schemas

All models are [Pydantic v2](https://docs.pydantic.dev/latest/) `BaseModel`
subclasses defined in `lib/db/models.py`.

---

## Enums

### Language

| Value       | String    |
|-------------|-----------|
| `FRENCH`    | `french`  |
| `ITALIAN`   | `italian` |

### SessionMode

| Value            | String            | Description                     |
|------------------|-------------------|---------------------------------|
| `LIVE_MISSION`   | `live_mission`    | Full mission with a scenario    |
| `REPAIR_DRILL`   | `repair_drill`    | Focused error-correction drill  |
| `PHRASE_COACH`   | `phrase_coach`    | Phrase practice only            |
| `REVIEW`         | `review`          | Session review                  |
| `COUPLE_MISSION` | `couple_mission`  | Joint two-learner mission       |

### MistakeType

| Value             | String            |
|-------------------|-------------------|
| `GRAMMAR`         | `grammar`         |
| `VOCABULARY`      | `vocabulary`      |
| `PRONUNCIATION`   | `pronunciation`   |
| `REGISTER`        | `register`        |
| `NATURALNESS`     | `naturalness`     |
| `COMPREHENSION`   | `comprehension`   |

### MistakeSeverity

| Value    | String   |
|----------|----------|
| `LOW`    | `low`    |
| `MEDIUM` | `medium` |
| `HIGH`   | `high`   |

### CorrectionLabel

| Value                          | String                          |
|--------------------------------|---------------------------------|
| `CORRECT`                      | `correct`                       |
| `UNDERSTANDABLE_BUT_UNNATURAL` | `understandable_but_unnatural`  |
| `INCORRECT`                    | `incorrect`                     |
| `TOO_FORMAL`                   | `too_formal`                    |
| `TOO_BLUNT`                    | `too_blunt`                     |
| `UNCOMMON_WORDING`             | `uncommon_wording`              |

### ScenarioCategory

| Value        | String       |
|--------------|--------------|
| `RESTAURANT` | `restaurant` |
| `CAFE`       | `cafe`       |
| `HOTEL`      | `hotel`      |
| `TRAIN`      | `train`      |
| `SHOPPING`   | `shopping`   |
| `PHARMACY`   | `pharmacy`   |
| `DIRECTIONS` | `directions` |
| `SMALL_TALK` | `small_talk` |
| `MUSEUM`     | `museum`     |
| `MARKET`     | `market`     |

### DifficultyLevel

| Value                | String               | Order |
|----------------------|----------------------|-------|
| `BEGINNER`           | `beginner`           | 1     |
| `ELEMENTARY`         | `elementary`         | 2     |
| `INTERMEDIATE`       | `intermediate`       | 3     |
| `UPPER_INTERMEDIATE` | `upper_intermediate` | 4     |
| `ADVANCED`           | `advanced`           | 5     |

---

## Models

### LearnerProfile

Captures an individual learner's state, preferences, and known weaknesses.

| Field                     | Type                   | Default                  | Description                                          |
|---------------------------|------------------------|--------------------------|------------------------------------------------------|
| `learner_id`              | `str`                  | auto-generated UUID      | Unique learner identifier                            |
| `name`                    | `str`                  | *(required)*             | Learner display name                                 |
| `target_languages`        | `List[Language]`       | *(required)*             | Languages the learner is studying                    |
| `estimated_french_level`  | `DifficultyLevel`      | `BEGINNER`               | Current estimated French proficiency                 |
| `estimated_italian_level` | `DifficultyLevel`      | `BEGINNER`               | Current estimated Italian proficiency                |
| `speaking_confidence`     | `float`                | `0.5`                    | Self-reported confidence, 0.0–1.0                    |
| `common_error_types`      | `List[MistakeType]`    | `[]`                     | Frequently occurring mistake categories              |
| `weak_scenarios`          | `List[str]`            | `[]`                     | Scenario categories the learner struggles with       |
| `strong_scenarios`        | `List[str]`            | `[]`                     | Scenario categories the learner performs well in     |
| `pronunciation_notes`     | `List[str]`            | `[]`                     | Notes on recurring pronunciation issues              |
| `preferred_modes`         | `List[SessionMode]`    | `[]`                     | Learner's preferred session modes                    |
| `trip_relevance_tags`     | `List[str]`            | `[]`                     | Trip-specific tags (destinations, contexts)          |
| `updated_at`              | `datetime`             | `utcnow()`               | Timestamp of last profile update                     |

### CoupleProfile

Links two learners for joint practice sessions.

| Field                    | Type           | Default             | Description                                      |
|--------------------------|----------------|---------------------|--------------------------------------------------|
| `couple_profile_id`      | `str`          | auto-generated UUID | Unique couple identifier                         |
| `learner_1_id`           | `str`          | *(required)*        | First learner's ID                               |
| `learner_2_id`           | `str`          | *(required)*        | Second learner's ID                              |
| `shared_trip_goals`      | `List[str]`    | `[]`                | Joint travel destinations or goals               |
| `shared_weak_scenarios`  | `List[str]`    | `[]`                | Scenarios both learners struggle with            |
| `shared_strong_scenarios`| `List[str]`    | `[]`                | Scenarios both learners handle well              |
| `handoff_patterns`       | `List[str]`    | `[]`                | Observed turn-taking patterns                    |
| `joint_session_count`    | `int`          | `0`                 | Number of completed joint sessions               |
| `joint_success_notes`    | `List[str]`    | `[]`                | Notes on collaborative successes                 |
| `updated_at`             | `datetime`     | `utcnow()`          | Timestamp of last update                         |

### Session

Represents a single coaching session from start to end.

| Field             | Type                       | Default             | Description                                        |
|-------------------|----------------------------|---------------------|----------------------------------------------------|
| `session_id`      | `str`                      | auto-generated UUID | Unique session identifier                          |
| `mode`            | `SessionMode`              | *(required)*        | Type of session                                    |
| `language`        | `Language`                 | *(required)*        | Target language for this session                   |
| `learner_ids`     | `List[str]`                | *(required)*        | Participating learner IDs (1 for solo, 2 for couple)|
| `scenario_id`     | `Optional[str]`            | `None`              | Active scenario ID (if applicable)                 |
| `transcript`      | `List[Dict[str, str]]`     | `[]`                | Conversation log: `{"role": "...", "content": "..."}`|
| `score_breakdown` | `Optional[Dict[str, float]]` | `None`           | Per-dimension scores after evaluation              |
| `summary`         | `Optional[str]`            | `None`              | Generated recap text                               |
| `next_drill`      | `Optional[str]`            | `None`              | Recommended follow-up drill                        |
| `created_at`      | `datetime`                 | `utcnow()`          | Session creation timestamp                         |

### Scenario

A real-world practice situation with goals and failure modes.

| Field               | Type                | Default             | Description                                     |
|---------------------|---------------------|---------------------|-------------------------------------------------|
| `scenario_id`       | `str`               | auto-generated UUID | Unique scenario identifier                      |
| `country`           | `str`               | *(required)*        | Country setting (e.g., `"France"`)              |
| `city`              | `str`               | *(required)*        | City setting (e.g., `"Paris"`)                  |
| `category`          | `ScenarioCategory`  | *(required)*        | Scenario type (restaurant, hotel, etc.)         |
| `difficulty`        | `DifficultyLevel`   | *(required)*        | Difficulty rating                               |
| `local_role`        | `str`               | *(required)*        | Persona description (e.g., `"patient waiter"`)  |
| `goal`              | `str`               | *(required)*        | Mission goal for the learner                    |
| `failure_modes`     | `List[str]`         | `[]`                | Common ways the learner might fail              |
| `pressure_elements` | `List[str]`         | `[]`                | Realistic stressors (noise, speed, etc.)        |
| `culture_notes`     | `List[str]`         | `[]`                | Relevant cultural tips                          |
| `language`          | `Language`          | *(required)*        | Target language for this scenario               |

### Mistake

A single error extracted from a session transcript.

| Field              | Type              | Default             | Description                                      |
|--------------------|-------------------|---------------------|--------------------------------------------------|
| `mistake_id`       | `str`             | auto-generated UUID | Unique mistake identifier                        |
| `learner_id`       | `str`             | *(required)*        | Learner who made the mistake                     |
| `session_id`       | `str`             | *(required)*        | Session where the mistake occurred               |
| `type`             | `MistakeType`     | *(required)*        | Category of mistake                              |
| `source_phrase`    | `str`             | *(required)*        | What the learner actually said                   |
| `corrected_phrase` | `str`             | *(required)*        | Correct or improved version                      |
| `explanation`      | `str`             | *(required)*        | Why it is a mistake and how to fix it            |
| `severity`         | `MistakeSeverity` | *(required)*        | Impact level (low / medium / high)               |
| `correction_label` | `CorrectionLabel` | *(required)*        | Fine-grained classification of the error         |
| `recurrence_count` | `int`             | `1`                 | How many times this exact mistake has been seen   |
| `last_seen`        | `datetime`        | `utcnow()`          | When the mistake was last recorded               |

### PhraseMastery

Tracks a learner's familiarity with a specific phrase over time.

| Field                    | Type                | Default   | Description                                   |
|--------------------------|---------------------|-----------|-----------------------------------------------|
| `learner_id`             | `str`               | *(required)* | Learner who practiced the phrase           |
| `phrase_id`              | `str`               | *(required)* | Unique phrase identifier                   |
| `phrase_text`            | `str`               | *(required)* | The phrase itself                          |
| `language`               | `Language`          | *(required)* | Language of the phrase                     |
| `familiarity_score`      | `float`             | `0.0`        | Overall familiarity, 0.0–1.0              |
| `success_under_pressure` | `float`             | `0.0`        | Success rate under time/stress, 0.0–1.0   |
| `last_practiced`         | `Optional[datetime]`| `None`       | Timestamp of last successful practice     |
| `last_failed`            | `Optional[datetime]`| `None`       | Timestamp of last failure                 |
| `notes`                  | `List[str]`         | `[]`         | Free-form notes about the learner's usage |

### CoupleSession

Extends a session with couple-specific metadata.

| Field              | Type                   | Default             | Description                                   |
|--------------------|------------------------|---------------------|-----------------------------------------------|
| `session_id`       | `str`                  | auto-generated UUID | Unique session identifier                     |
| `learner_1_id`     | `str`                  | *(required)*        | First learner's ID                            |
| `learner_2_id`     | `str`                  | *(required)*        | Second learner's ID                           |
| `handoff_events`   | `List[Dict[str, str]]` | `[]`                | Turn-taking log (who spoke when)              |
| `joint_score`      | `Optional[float]`      | `None`              | Combined/average session score                |
| `joint_weaknesses` | `List[str]`            | `[]`                | Dimensions both learners scored low on        |
| `joint_strengths`  | `List[str]`            | `[]`                | Dimensions both learners scored high on       |

### ScoreBreakdown

Detailed per-dimension scoring rubric for a session.

| Field                    | Type    | Range   | Weight | Description                        |
|--------------------------|---------|---------|--------|------------------------------------|
| `comprehensibility`      | `float` | 1.0–5.0 | 0.20   | Clarity of speech to a native      |
| `task_completion`        | `float` | 1.0–5.0 | 0.20   | Degree the mission goal was met    |
| `grammar`                | `float` | 1.0–5.0 | 0.10   | Grammatical accuracy               |
| `naturalness`            | `float` | 1.0–5.0 | 0.10   | Native-like fluency & idiom usage  |
| `politeness_register`    | `float` | 1.0–5.0 | 0.10   | Appropriate formality level        |
| `recovery`               | `float` | 1.0–5.0 | 0.15   | Ability to self-correct on the fly |
| `confidence_hesitation`  | `float` | 1.0–5.0 | 0.15   | Confidence vs. hesitation balance  |

**Computed properties:**

| Property          | Return Type | Description                                    |
|-------------------|-------------|------------------------------------------------|
| `weighted_average`| `float`     | Weighted sum across all 7 dimensions (1.0–5.0) |
| `overall_rating`  | `str`       | Human-readable label derived from weighted avg |
