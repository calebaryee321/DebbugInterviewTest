"""Shared fixtures for Travel Language Coach tests."""

import pytest

from lib.db.models import (
    CoupleProfile,
    DifficultyLevel,
    Language,
    LearnerProfile,
    Mistake,
    MistakeSeverity,
    MistakeType,
    CorrectionLabel,
    PhraseMastery,
    Scenario,
    ScenarioCategory,
    ScoreBreakdown,
    Session,
    SessionMode,
)
from agents.memory.agent import MemoryAgent
from lib.scoring.engine import ScoringEngine


@pytest.fixture
def sample_learner_profile() -> LearnerProfile:
    """A LearnerProfile for 'Caleb' studying French and Italian at BEGINNER."""
    return LearnerProfile(
        learner_id="caleb-001",
        name="Caleb",
        target_languages=[Language.FRENCH, Language.ITALIAN],
        estimated_french_level=DifficultyLevel.BEGINNER,
        estimated_italian_level=DifficultyLevel.BEGINNER,
        speaking_confidence=0.4,
    )


@pytest.fixture
def sample_wife_profile() -> LearnerProfile:
    """A LearnerProfile for 'Wife' studying French and Italian at BEGINNER."""
    return LearnerProfile(
        learner_id="wife-001",
        name="Wife",
        target_languages=[Language.FRENCH, Language.ITALIAN],
        estimated_french_level=DifficultyLevel.BEGINNER,
        estimated_italian_level=DifficultyLevel.BEGINNER,
        speaking_confidence=0.5,
    )


@pytest.fixture
def sample_couple_profile(
    sample_learner_profile: LearnerProfile,
    sample_wife_profile: LearnerProfile,
) -> CoupleProfile:
    """A CoupleProfile linking Caleb and Wife."""
    return CoupleProfile(
        learner_1_id=sample_learner_profile.learner_id,
        learner_2_id=sample_wife_profile.learner_id,
        shared_trip_goals=["Order food confidently", "Navigate train stations"],
    )


@pytest.fixture
def sample_scenario() -> Scenario:
    """A beginner café scenario in Paris, France."""
    return Scenario(
        scenario_id="test-scenario-001",
        country="France",
        city="Paris",
        category=ScenarioCategory.CAFE,
        difficulty=DifficultyLevel.BEGINNER,
        local_role="patient waiter",
        goal="Order a coffee and a croissant",
        failure_modes=["Forgetting to say Bonjour"],
        culture_notes=["Always greet with Bonjour"],
        language=Language.FRENCH,
    )


@pytest.fixture
def sample_session() -> Session:
    """A LIVE_MISSION session in French with a sample transcript."""
    return Session(
        session_id="test-session-001",
        mode=SessionMode.LIVE_MISSION,
        language=Language.FRENCH,
        learner_ids=["caleb-001"],
        scenario_id="test-scenario-001",
        transcript=[
            {"role": "tutor", "content": "Bonjour! Bienvenue au café."},
            {"role": "learner", "content": "Bonjour, je voudrais un café."},
            {"role": "tutor", "content": "Très bien! Un café, tout de suite."},
            {"role": "learner", "content": "Et un croissant, s'il vous plaît."},
        ],
    )


@pytest.fixture
def sample_score_breakdown() -> ScoreBreakdown:
    """A realistic ScoreBreakdown with varied scores."""
    return ScoreBreakdown(
        comprehensibility=4.0,
        task_completion=3.5,
        grammar=3.0,
        naturalness=2.5,
        politeness_register=4.0,
        recovery=3.5,
        confidence_hesitation=3.0,
    )


@pytest.fixture
def memory_agent() -> MemoryAgent:
    """A freshly initialised MemoryAgent."""
    return MemoryAgent()


@pytest.fixture
def scoring_engine() -> ScoringEngine:
    """A ScoringEngine instance."""
    return ScoringEngine()
