"""Tests for the EvaluatorAgent."""

import pytest

from lib.db.models import (
    CorrectionLabel,
    Language,
    LearnerProfile,
    Mistake,
    MistakeSeverity,
    MistakeType,
    ScoreBreakdown,
    Session,
    SessionMode,
)
from agents.evaluator.agent import EvaluatorAgent


@pytest.fixture
def evaluator():
    return EvaluatorAgent()


@pytest.fixture
def _session_with_transcript():
    return Session(
        mode=SessionMode.LIVE_MISSION,
        language=Language.FRENCH,
        learner_ids=["caleb-001"],
        transcript=[
            {"role": "tutor", "content": "Bonjour! Bienvenue au café."},
            {"role": "learner", "content": "Bonjour, je voudrais un café."},
            {"role": "tutor", "content": "Très bien! Un café, tout de suite."},
            {"role": "learner", "content": "Et un croissant, s'il vous plaît."},
            {"role": "tutor", "content": "Voilà! Autre chose?"},
            {"role": "learner", "content": "Non merci, l'addition s'il vous plaît."},
        ],
    )


@pytest.fixture
def _sample_mistakes():
    return [
        Mistake(
            learner_id="caleb-001",
            session_id="sess-001",
            type=MistakeType.GRAMMAR,
            source_phrase="Je veux un café",
            corrected_phrase="Je voudrais un café",
            explanation="Use conditional for politeness",
            severity=MistakeSeverity.MEDIUM,
            correction_label=CorrectionLabel.TOO_BLUNT,
        ),
        Mistake(
            learner_id="caleb-001",
            session_id="sess-001",
            type=MistakeType.VOCABULARY,
            source_phrase="le facture",
            corrected_phrase="l'addition",
            explanation="Wrong word for bill",
            severity=MistakeSeverity.LOW,
            correction_label=CorrectionLabel.INCORRECT,
        ),
    ]


class TestEvaluateSession:
    def test_returns_score_and_mistakes(self, evaluator, _session_with_transcript):
        score, mistakes = evaluator.evaluate_session(_session_with_transcript)
        assert isinstance(score, ScoreBreakdown)
        assert isinstance(mistakes, list)
        # Heuristic scoring should give reasonable scores
        assert 1.0 <= score.comprehensibility <= 5.0
        assert 1.0 <= score.task_completion <= 5.0

    def test_score_reflects_learner_turns(self, evaluator):
        # More learner turns → higher base score
        many_turns = Session(
            mode=SessionMode.LIVE_MISSION,
            language=Language.FRENCH,
            learner_ids=["caleb-001"],
            transcript=[
                {"role": "learner", "content": f"Turn {i}"}
                for i in range(10)
            ],
        )
        score, _ = evaluator.evaluate_session(many_turns)
        assert score.task_completion >= 3.0


class TestExtractMistakes:
    def test_returns_list(self, evaluator):
        transcript = [
            {"role": "learner", "content": "Je veux un café"},
            {"role": "tutor", "content": "Bien sûr!"},
        ]
        mistakes = evaluator.extract_mistakes(transcript, "french")
        # Without a real LLM, returns empty list
        assert isinstance(mistakes, list)
        assert len(mistakes) == 0


class TestGenerateRecap:
    def test_returns_string(self, evaluator, _session_with_transcript, sample_score_breakdown, _sample_mistakes):
        recap = evaluator.generate_recap(
            _session_with_transcript, sample_score_breakdown, _sample_mistakes
        )
        assert isinstance(recap, str)
        assert len(recap) > 0

    def test_recap_without_mistakes(self, evaluator, _session_with_transcript, sample_score_breakdown):
        recap = evaluator.generate_recap(
            _session_with_transcript, sample_score_breakdown, []
        )
        assert isinstance(recap, str)
        assert len(recap) > 0


class TestRecommendNextDrill:
    def test_returns_string(self, evaluator, sample_score_breakdown, _sample_mistakes, sample_learner_profile):
        result = evaluator.recommend_next_drill(
            sample_score_breakdown, _sample_mistakes, sample_learner_profile
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_with_no_mistakes(self, evaluator, sample_score_breakdown, sample_learner_profile):
        result = evaluator.recommend_next_drill(
            sample_score_breakdown, [], sample_learner_profile
        )
        assert isinstance(result, str)
