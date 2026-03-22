"""Tests for the MemoryAgent."""

import pytest

from lib.db.models import (
    CorrectionLabel,
    Language,
    LearnerProfile,
    Mistake,
    MistakeSeverity,
    MistakeType,
    PhraseMastery,
    ScoreBreakdown,
    Session,
    SessionMode,
)
from agents.memory.agent import MemoryAgent


class TestStoreAndRetrieveProfile:
    def test_store_and_retrieve_learner_profile(self, memory_agent, sample_learner_profile):
        memory_agent.store_learner_profile(sample_learner_profile)
        retrieved = memory_agent.get_learner_profile("caleb-001")
        assert retrieved is not None
        assert retrieved.name == "Caleb"
        assert retrieved.learner_id == "caleb-001"

    def test_get_nonexistent_profile_returns_none(self, memory_agent):
        assert memory_agent.get_learner_profile("nonexistent") is None

    def test_store_and_retrieve_couple_profile(self, memory_agent, sample_couple_profile):
        memory_agent.store_couple_profile(sample_couple_profile)
        retrieved = memory_agent.get_couple_profile(
            sample_couple_profile.couple_profile_id
        )
        assert retrieved is not None
        assert retrieved.learner_1_id == "caleb-001"
        assert retrieved.learner_2_id == "wife-001"

    def test_get_nonexistent_couple_returns_none(self, memory_agent):
        assert memory_agent.get_couple_profile("nonexistent") is None


class TestRecordMistake:
    @pytest.fixture
    def _mistake(self):
        return Mistake(
            learner_id="caleb-001",
            session_id="sess-001",
            type=MistakeType.GRAMMAR,
            source_phrase="Je veux un café",
            corrected_phrase="Je voudrais un café",
            explanation="Use conditional for politeness",
            severity=MistakeSeverity.MEDIUM,
            correction_label=CorrectionLabel.TOO_BLUNT,
        )

    def test_record_and_retrieve(self, memory_agent, _mistake):
        memory_agent.record_mistake(_mistake)
        mistakes = memory_agent.get_learner_mistakes("caleb-001")
        assert len(mistakes) == 1
        assert mistakes[0].source_phrase == "Je veux un café"

    def test_recurrence_count_increments_for_same_mistake(self, memory_agent, _mistake):
        memory_agent.record_mistake(_mistake)
        # Record same type + source_phrase again
        duplicate = Mistake(
            learner_id="caleb-001",
            session_id="sess-002",
            type=MistakeType.GRAMMAR,
            source_phrase="Je veux un café",
            corrected_phrase="Je voudrais un café",
            explanation="Use conditional for politeness",
            severity=MistakeSeverity.MEDIUM,
            correction_label=CorrectionLabel.TOO_BLUNT,
        )
        memory_agent.record_mistake(duplicate)
        mistakes = memory_agent.get_learner_mistakes("caleb-001")
        assert len(mistakes) == 1
        assert mistakes[0].recurrence_count == 2

    def test_different_mistakes_stored_separately(self, memory_agent, _mistake):
        memory_agent.record_mistake(_mistake)
        other = Mistake(
            learner_id="caleb-001",
            session_id="sess-002",
            type=MistakeType.VOCABULARY,
            source_phrase="le facture",
            corrected_phrase="l'addition",
            explanation="Wrong word for bill",
            severity=MistakeSeverity.LOW,
            correction_label=CorrectionLabel.INCORRECT,
        )
        memory_agent.record_mistake(other)
        mistakes = memory_agent.get_learner_mistakes("caleb-001")
        assert len(mistakes) == 2

    def test_get_learner_mistakes_with_limit(self, memory_agent):
        for i in range(5):
            memory_agent.record_mistake(
                Mistake(
                    learner_id="caleb-001",
                    session_id=f"sess-{i}",
                    type=MistakeType.GRAMMAR,
                    source_phrase=f"phrase-{i}",
                    corrected_phrase=f"corrected-{i}",
                    explanation="test",
                    severity=MistakeSeverity.LOW,
                    correction_label=CorrectionLabel.INCORRECT,
                )
            )
        limited = memory_agent.get_learner_mistakes("caleb-001", limit=3)
        assert len(limited) == 3


class TestPhraseMastery:
    def test_update_and_get_weak_phrases(self, memory_agent):
        pm = PhraseMastery(
            learner_id="caleb-001",
            phrase_id="ph-001",
            phrase_text="Bonjour",
            language=Language.FRENCH,
            familiarity_score=0.3,
        )
        memory_agent.update_phrase_mastery(pm)
        weak = memory_agent.get_weak_phrases("caleb-001")
        assert len(weak) == 1
        assert weak[0].phrase_text == "Bonjour"

    def test_get_weak_phrases_with_threshold(self, memory_agent):
        memory_agent.update_phrase_mastery(
            PhraseMastery(
                learner_id="caleb-001",
                phrase_id="ph-001",
                phrase_text="Bonjour",
                language=Language.FRENCH,
                familiarity_score=0.7,
            )
        )
        memory_agent.update_phrase_mastery(
            PhraseMastery(
                learner_id="caleb-001",
                phrase_id="ph-002",
                phrase_text="Merci",
                language=Language.FRENCH,
                familiarity_score=0.2,
            )
        )
        weak_low = memory_agent.get_weak_phrases("caleb-001", threshold=0.5)
        assert len(weak_low) == 1
        assert weak_low[0].phrase_text == "Merci"

        weak_high = memory_agent.get_weak_phrases("caleb-001", threshold=0.8)
        assert len(weak_high) == 2

    def test_update_existing_phrase_mastery(self, memory_agent):
        pm1 = PhraseMastery(
            learner_id="caleb-001",
            phrase_id="ph-001",
            phrase_text="Bonjour",
            language=Language.FRENCH,
            familiarity_score=0.3,
        )
        memory_agent.update_phrase_mastery(pm1)

        pm2 = PhraseMastery(
            learner_id="caleb-001",
            phrase_id="ph-001",
            phrase_text="Bonjour",
            language=Language.FRENCH,
            familiarity_score=0.8,
        )
        memory_agent.update_phrase_mastery(pm2)

        weak = memory_agent.get_weak_phrases("caleb-001", threshold=0.5)
        assert len(weak) == 0  # Score updated to 0.8, no longer weak


class TestUpdateAfterSession:
    def test_updates_profile(self, memory_agent, sample_learner_profile, sample_session):
        memory_agent.store_learner_profile(sample_learner_profile)
        score = ScoreBreakdown(
            comprehensibility=3.5, task_completion=3.0, grammar=2.5,
            naturalness=3.0, politeness_register=3.5, recovery=3.0,
            confidence_hesitation=3.0,
        )
        mistakes = [
            Mistake(
                learner_id="caleb-001",
                session_id="test-session-001",
                type=MistakeType.GRAMMAR,
                source_phrase="Je veux",
                corrected_phrase="Je voudrais",
                explanation="Politeness",
                severity=MistakeSeverity.MEDIUM,
                correction_label=CorrectionLabel.TOO_BLUNT,
            )
        ]
        memory_agent.update_after_session(sample_session, score, mistakes)

        # Mistakes should be recorded
        recorded = memory_agent.get_learner_mistakes("caleb-001")
        assert len(recorded) == 1


class TestGetLearnerHistory:
    def test_returns_correct_structure(self, memory_agent, sample_session):
        score = ScoreBreakdown(
            comprehensibility=3.5, task_completion=3.0, grammar=2.5,
            naturalness=3.0, politeness_register=3.5, recovery=3.0,
            confidence_hesitation=3.0,
        )
        memory_agent.update_after_session(sample_session, score, [])
        history = memory_agent.get_learner_history("caleb-001")

        assert "learner_id" in history
        assert "total_sessions" in history
        assert "average_score" in history
        assert "total_mistakes" in history
        assert "recurring_mistakes" in history
        assert "weak_phrase_count" in history
        assert "recent_sessions" in history
        assert history["total_sessions"] == 1
        assert history["learner_id"] == "caleb-001"

    def test_empty_history(self, memory_agent):
        history = memory_agent.get_learner_history("nobody")
        assert history["total_sessions"] == 0
        assert history["average_score"] == 0.0
