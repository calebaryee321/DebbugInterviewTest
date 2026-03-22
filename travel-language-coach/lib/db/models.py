"""Data models for the Travel Language Coach application.

Defines Pydantic v2 models for learner profiles, sessions, scenarios,
mistakes, phrase mastery tracking, and scoring.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Language(str, Enum):
    """Supported target languages."""

    FRENCH = "french"
    ITALIAN = "italian"


class SessionMode(str, Enum):
    """Available coaching session modes."""

    LIVE_MISSION = "live_mission"
    REPAIR_DRILL = "repair_drill"
    PHRASE_COACH = "phrase_coach"
    REVIEW = "review"
    COUPLE_MISSION = "couple_mission"


class MistakeType(str, Enum):
    """Categories of language mistakes."""

    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    REGISTER = "register"
    NATURALNESS = "naturalness"
    COMPREHENSION = "comprehension"


class MistakeSeverity(str, Enum):
    """Severity level of a recorded mistake."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CorrectionLabel(str, Enum):
    """Classification labels applied to learner utterances."""

    CORRECT = "correct"
    UNDERSTANDABLE_BUT_UNNATURAL = "understandable_but_unnatural"
    INCORRECT = "incorrect"
    TOO_FORMAL = "too_formal"
    TOO_BLUNT = "too_blunt"
    UNCOMMON_WORDING = "uncommon_wording"


class ScenarioCategory(str, Enum):
    """Real-world scenario categories for practice missions."""

    RESTAURANT = "restaurant"
    CAFE = "cafe"
    HOTEL = "hotel"
    TRAIN = "train"
    SHOPPING = "shopping"
    PHARMACY = "pharmacy"
    DIRECTIONS = "directions"
    SMALL_TALK = "small_talk"
    MUSEUM = "museum"
    MARKET = "market"


class DifficultyLevel(str, Enum):
    """CEFR-inspired difficulty levels."""

    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class LearnerProfile(BaseModel):
    """Profile storing a learner's abilities, preferences, and history."""

    learner_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    target_languages: List[Language]
    estimated_french_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_italian_level: DifficultyLevel = DifficultyLevel.BEGINNER
    speaking_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Self-reported confidence (0-1)"
    )
    common_error_types: List[MistakeType] = Field(default_factory=list)
    weak_scenarios: List[str] = Field(default_factory=list)
    strong_scenarios: List[str] = Field(default_factory=list)
    pronunciation_notes: List[str] = Field(default_factory=list)
    preferred_modes: List[SessionMode] = Field(default_factory=list)
    trip_relevance_tags: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CoupleProfile(BaseModel):
    """Joint profile for two learners practicing together."""

    couple_profile_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_1_id: str
    learner_2_id: str
    shared_trip_goals: List[str] = Field(default_factory=list)
    shared_weak_scenarios: List[str] = Field(default_factory=list)
    shared_strong_scenarios: List[str] = Field(default_factory=list)
    handoff_patterns: List[str] = Field(default_factory=list)
    joint_session_count: int = 0
    joint_success_notes: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Scenario(BaseModel):
    """A real-world scenario used for live missions and drills."""

    scenario_id: str = Field(default_factory=lambda: str(uuid4()))
    country: str
    city: str
    category: ScenarioCategory
    difficulty: DifficultyLevel
    local_role: str = Field(description="Persona description, e.g. 'patient waiter'")
    goal: str = Field(description="Mission goal description")
    failure_modes: List[str] = Field(default_factory=list)
    pressure_elements: List[str] = Field(default_factory=list)
    culture_notes: List[str] = Field(default_factory=list)
    language: Language


class Session(BaseModel):
    """A single coaching session."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: SessionMode
    language: Language
    learner_ids: List[str]
    scenario_id: Optional[str] = None
    transcript: List[Dict[str, str]] = Field(
        default_factory=list,
        description='List of {"role": "...", "content": "..."} entries',
    )
    score_breakdown: Optional[Dict[str, float]] = None
    summary: Optional[str] = None
    next_drill: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Mistake(BaseModel):
    """A recorded learner mistake with correction details."""

    mistake_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_id: str
    session_id: str
    type: MistakeType
    source_phrase: str
    corrected_phrase: str
    explanation: str
    severity: MistakeSeverity
    correction_label: CorrectionLabel
    recurrence_count: int = 1
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class PhraseMastery(BaseModel):
    """Tracks a learner's mastery of a specific phrase."""

    learner_id: str
    phrase_id: str
    phrase_text: str
    language: Language
    familiarity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Familiarity score (0-1)"
    )
    success_under_pressure: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Success under pressure (0-1)"
    )
    last_practiced: Optional[datetime] = None
    last_failed: Optional[datetime] = None
    notes: List[str] = Field(default_factory=list)


class CoupleSession(BaseModel):
    """Metadata for a joint couple practice session."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_1_id: str
    learner_2_id: str
    handoff_events: List[Dict[str, str]] = Field(default_factory=list)
    joint_score: Optional[float] = None
    joint_weaknesses: List[str] = Field(default_factory=list)
    joint_strengths: List[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """Detailed scoring rubric for a session (each dimension 1.0-5.0)."""

    comprehensibility: float = Field(ge=1.0, le=5.0)
    task_completion: float = Field(ge=1.0, le=5.0)
    grammar: float = Field(ge=1.0, le=5.0)
    naturalness: float = Field(ge=1.0, le=5.0)
    politeness_register: float = Field(ge=1.0, le=5.0)
    recovery: float = Field(ge=1.0, le=5.0)
    confidence_hesitation: float = Field(ge=1.0, le=5.0)

    @property
    def weighted_average(self) -> float:
        """Return the weighted average across all scoring dimensions."""
        return (
            self.comprehensibility * 0.20
            + self.task_completion * 0.20
            + self.recovery * 0.15
            + self.grammar * 0.10
            + self.naturalness * 0.10
            + self.politeness_register * 0.10
            + self.confidence_hesitation * 0.15
        )

    @property
    def overall_rating(self) -> str:
        """Human-readable rating derived from the weighted average."""
        avg = self.weighted_average
        if avg < 2.0:
            return "Needs Practice"
        if avg < 3.0:
            return "Developing"
        if avg < 4.0:
            return "Functional"
        return "Strong"
