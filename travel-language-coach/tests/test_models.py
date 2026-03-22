"""Tests for all data models in lib.db.models."""

import pytest
from datetime import datetime

from lib.db.models import (
    CorrectionLabel,
    CoupleProfile,
    CoupleSession,
    DifficultyLevel,
    Language,
    LearnerProfile,
    Mistake,
    MistakeSeverity,
    MistakeType,
    PhraseMastery,
    Scenario,
    ScenarioCategory,
    ScoreBreakdown,
    Session,
    SessionMode,
)


# ── LearnerProfile ──────────────────────────────────────────────────


class TestLearnerProfile:
    def test_creation_with_defaults(self):
        profile = LearnerProfile(
            name="Test",
            target_languages=[Language.FRENCH],
        )
        assert profile.name == "Test"
        assert profile.learner_id  # auto-generated UUID
        assert profile.estimated_french_level == DifficultyLevel.BEGINNER
        assert profile.estimated_italian_level == DifficultyLevel.BEGINNER
        assert profile.speaking_confidence == 0.5
        assert profile.common_error_types == []
        assert profile.weak_scenarios == []
        assert profile.strong_scenarios == []

    def test_creation_with_custom_values(self):
        profile = LearnerProfile(
            learner_id="custom-id",
            name="Custom",
            target_languages=[Language.FRENCH, Language.ITALIAN],
            estimated_french_level=DifficultyLevel.INTERMEDIATE,
            estimated_italian_level=DifficultyLevel.ELEMENTARY,
            speaking_confidence=0.8,
            common_error_types=[MistakeType.GRAMMAR],
            weak_scenarios=["restaurant"],
            strong_scenarios=["hotel"],
        )
        assert profile.learner_id == "custom-id"
        assert profile.estimated_french_level == DifficultyLevel.INTERMEDIATE
        assert profile.speaking_confidence == 0.8
        assert MistakeType.GRAMMAR in profile.common_error_types


# ── CoupleProfile ───────────────────────────────────────────────────


class TestCoupleProfile:
    def test_creation(self, sample_learner_profile, sample_wife_profile):
        cp = CoupleProfile(
            learner_1_id=sample_learner_profile.learner_id,
            learner_2_id=sample_wife_profile.learner_id,
            shared_trip_goals=["Navigate Paris"],
        )
        assert cp.learner_1_id == "caleb-001"
        assert cp.learner_2_id == "wife-001"
        assert "Navigate Paris" in cp.shared_trip_goals
        assert cp.joint_session_count == 0


# ── Scenario ─────────────────────────────────────────────────────────


class TestScenario:
    def test_creation_with_all_fields(self, sample_scenario):
        s = sample_scenario
        assert s.country == "France"
        assert s.city == "Paris"
        assert s.category == ScenarioCategory.CAFE
        assert s.difficulty == DifficultyLevel.BEGINNER
        assert s.local_role == "patient waiter"
        assert s.goal == "Order a coffee and a croissant"
        assert s.language == Language.FRENCH
        assert len(s.failure_modes) == 1
        assert len(s.culture_notes) == 1


# ── Session ──────────────────────────────────────────────────────────


class TestSession:
    def test_creation_with_transcript(self, sample_session):
        s = sample_session
        assert s.mode == SessionMode.LIVE_MISSION
        assert s.language == Language.FRENCH
        assert len(s.transcript) == 4
        assert s.transcript[0]["role"] == "tutor"
        assert s.score_breakdown is None


# ── Mistake ──────────────────────────────────────────────────────────


class TestMistake:
    def test_creation_with_all_fields(self):
        m = Mistake(
            learner_id="caleb-001",
            session_id="sess-001",
            type=MistakeType.GRAMMAR,
            source_phrase="Je veux un café",
            corrected_phrase="Je voudrais un café",
            explanation="Use conditional for polite requests",
            severity=MistakeSeverity.MEDIUM,
            correction_label=CorrectionLabel.TOO_BLUNT,
        )
        assert m.type == MistakeType.GRAMMAR
        assert m.severity == MistakeSeverity.MEDIUM
        assert m.correction_label == CorrectionLabel.TOO_BLUNT
        assert m.recurrence_count == 1
        assert m.source_phrase == "Je veux un café"
        assert m.corrected_phrase == "Je voudrais un café"


# ── PhraseMastery ────────────────────────────────────────────────────


class TestPhraseMastery:
    def test_creation(self):
        pm = PhraseMastery(
            learner_id="caleb-001",
            phrase_id="ph-001",
            phrase_text="Bonjour",
            language=Language.FRENCH,
            familiarity_score=0.3,
            success_under_pressure=0.2,
        )
        assert pm.familiarity_score == 0.3
        assert pm.success_under_pressure == 0.2
        assert pm.last_practiced is None
        assert pm.notes == []


# ── CoupleSession ───────────────────────────────────────────────────


class TestCoupleSession:
    def test_creation(self):
        cs = CoupleSession(
            learner_1_id="caleb-001",
            learner_2_id="wife-001",
        )
        assert cs.learner_1_id == "caleb-001"
        assert cs.joint_score is None
        assert cs.handoff_events == []
        assert cs.joint_weaknesses == []


# ── ScoreBreakdown ───────────────────────────────────────────────────


class TestScoreBreakdown:
    def test_creation(self, sample_score_breakdown):
        sb = sample_score_breakdown
        assert sb.comprehensibility == 4.0
        assert sb.grammar == 3.0

    def test_weighted_average_computation(self, sample_score_breakdown):
        sb = sample_score_breakdown
        expected = (
            4.0 * 0.20   # comprehensibility
            + 3.5 * 0.20  # task_completion
            + 3.5 * 0.15  # recovery
            + 3.0 * 0.10  # grammar
            + 2.5 * 0.10  # naturalness
            + 4.0 * 0.10  # politeness_register
            + 3.0 * 0.15  # confidence_hesitation
        )
        assert abs(sb.weighted_average - expected) < 1e-9

    def test_overall_rating_needs_practice(self):
        sb = ScoreBreakdown(
            comprehensibility=1.0, task_completion=1.0, grammar=1.0,
            naturalness=1.0, politeness_register=1.0, recovery=1.0,
            confidence_hesitation=1.0,
        )
        assert sb.overall_rating == "Needs Practice"

    def test_overall_rating_developing(self):
        sb = ScoreBreakdown(
            comprehensibility=2.5, task_completion=2.5, grammar=2.5,
            naturalness=2.5, politeness_register=2.5, recovery=2.5,
            confidence_hesitation=2.5,
        )
        assert sb.overall_rating == "Developing"

    def test_overall_rating_functional(self):
        sb = ScoreBreakdown(
            comprehensibility=3.5, task_completion=3.5, grammar=3.5,
            naturalness=3.5, politeness_register=3.5, recovery=3.5,
            confidence_hesitation=3.5,
        )
        assert sb.overall_rating == "Functional"

    def test_overall_rating_strong(self):
        sb = ScoreBreakdown(
            comprehensibility=5.0, task_completion=5.0, grammar=5.0,
            naturalness=5.0, politeness_register=5.0, recovery=5.0,
            confidence_hesitation=5.0,
        )
        assert sb.overall_rating == "Strong"


# ── Enum coverage ────────────────────────────────────────────────────


class TestEnums:
    def test_language_values(self):
        assert Language.FRENCH.value == "french"
        assert Language.ITALIAN.value == "italian"
        assert len(Language) == 2

    def test_session_mode_values(self):
        expected = {"live_mission", "repair_drill", "phrase_coach", "review", "couple_mission"}
        assert {m.value for m in SessionMode} == expected

    def test_mistake_type_values(self):
        expected = {"grammar", "vocabulary", "pronunciation", "register", "naturalness", "comprehension"}
        assert {m.value for m in MistakeType} == expected

    def test_mistake_severity_values(self):
        assert {s.value for s in MistakeSeverity} == {"low", "medium", "high"}

    def test_correction_label_values(self):
        expected = {
            "correct", "understandable_but_unnatural", "incorrect",
            "too_formal", "too_blunt", "uncommon_wording",
        }
        assert {c.value for c in CorrectionLabel} == expected

    def test_scenario_category_values(self):
        assert len(ScenarioCategory) == 10

    def test_difficulty_level_values(self):
        expected = {"beginner", "elementary", "intermediate", "upper_intermediate", "advanced"}
        assert {d.value for d in DifficultyLevel} == expected


# ── Serialization ────────────────────────────────────────────────────


class TestSerialization:
    def test_learner_profile_model_dump(self, sample_learner_profile):
        data = sample_learner_profile.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "Caleb"
        assert data["learner_id"] == "caleb-001"

    def test_scenario_model_dump(self, sample_scenario):
        data = sample_scenario.model_dump()
        assert data["country"] == "France"
        assert data["category"] == "cafe"

    def test_session_model_dump(self, sample_session):
        data = sample_session.model_dump()
        assert data["mode"] == "live_mission"
        assert len(data["transcript"]) == 4

    def test_score_breakdown_model_dump(self, sample_score_breakdown):
        data = sample_score_breakdown.model_dump()
        assert "comprehensibility" in data
        assert "grammar" in data
