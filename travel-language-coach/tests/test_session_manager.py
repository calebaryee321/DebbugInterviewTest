"""Tests for the SessionManager."""

import pytest

from lib.db.models import (
    DifficultyLevel,
    Language,
    LearnerProfile,
    Scenario,
    ScenarioCategory,
    Session,
    SessionMode,
)
from lib.orchestration.session_manager import SessionManager
from lib.scoring.engine import ScoringEngine
from agents.evaluator.agent import EvaluatorAgent
from agents.memory.agent import MemoryAgent
from agents.phrase_retrieval.agent import PhraseRetrievalAgent
from agents.scenario.agent import ScenarioAgent
from agents.tutor.agent import TutorAgent


@pytest.fixture
def _session_manager():
    """Build a SessionManager with all agents wired up."""
    scenarios = [
        Scenario(
            scenario_id="fr-cafe-1",
            country="France",
            city="Paris",
            category=ScenarioCategory.CAFE,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="waiter",
            goal="Order coffee",
            language=Language.FRENCH,
        ),
    ]
    memory = MemoryAgent()
    scenario = ScenarioAgent(scenarios=scenarios)
    phrase = PhraseRetrievalAgent()
    tutor = TutorAgent()
    evaluator = EvaluatorAgent()
    engine = ScoringEngine()

    # Seed a learner profile
    profile = LearnerProfile(
        learner_id="caleb-001",
        name="Caleb",
        target_languages=[Language.FRENCH],
    )
    memory.store_learner_profile(profile)

    return SessionManager(
        memory_agent=memory,
        scenario_agent=scenario,
        phrase_retrieval_agent=phrase,
        tutor_agent=tutor,
        evaluator_agent=evaluator,
        scoring_engine=engine,
    )


class TestCreateSession:
    def test_returns_session(self, _session_manager):
        session = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        assert isinstance(session, Session)
        assert session.language == Language.FRENCH
        assert session.mode == SessionMode.LIVE_MISSION
        assert "caleb-001" in session.learner_ids

    def test_session_stored(self, _session_manager):
        session = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        retrieved = _session_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id


class TestAddToTranscript:
    def test_adds_messages(self, _session_manager):
        session = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        _session_manager.add_to_transcript(session.session_id, "tutor", "Bonjour!")
        _session_manager.add_to_transcript(session.session_id, "learner", "Bonjour, un café.")

        retrieved = _session_manager.get_session(session.session_id)
        assert len(retrieved.transcript) == 2
        assert retrieved.transcript[0]["role"] == "tutor"
        assert retrieved.transcript[1]["content"] == "Bonjour, un café."

    def test_raises_for_invalid_session(self, _session_manager):
        with pytest.raises(KeyError):
            _session_manager.add_to_transcript("bad-id", "tutor", "Hello")


class TestGetSession:
    def test_retrieves_correct_session(self, _session_manager):
        session = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        result = _session_manager.get_session(session.session_id)
        assert result is not None
        assert result.session_id == session.session_id

    def test_returns_none_for_missing(self, _session_manager):
        assert _session_manager.get_session("nonexistent") is None


class TestEndSession:
    def test_returns_recap_dict(self, _session_manager):
        session = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        _session_manager.add_to_transcript(session.session_id, "tutor", "Bonjour!")
        _session_manager.add_to_transcript(session.session_id, "learner", "Un café.")

        recap = _session_manager.end_session(session.session_id)
        assert "session_id" in recap
        assert "score_breakdown" in recap
        assert "mistakes" in recap
        assert "recap_text" in recap
        assert "next_drill" in recap
        assert "rating" in recap
        assert recap["session_id"] == session.session_id


class TestGetActiveSessions:
    def test_returns_active(self, _session_manager):
        s1 = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        s2 = _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.REVIEW,
        )
        active = _session_manager.get_active_sessions()
        assert len(active) == 2

        # End one session
        _session_manager.add_to_transcript(s1.session_id, "learner", "test")
        _session_manager.end_session(s1.session_id)
        active = _session_manager.get_active_sessions()
        assert len(active) == 1


class TestGetLearnerSessions:
    def test_returns_learner_sessions(self, _session_manager):
        _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.LIVE_MISSION,
        )
        _session_manager.create_session(
            learner_id="caleb-001",
            language=Language.FRENCH,
            mode=SessionMode.REVIEW,
        )
        sessions = _session_manager.get_learner_sessions("caleb-001")
        assert len(sessions) == 2

    def test_returns_empty_for_unknown_learner(self, _session_manager):
        sessions = _session_manager.get_learner_sessions("unknown")
        assert sessions == []
