"""Tests for the ScoringEngine."""

import pytest

from lib.db.models import ScoreBreakdown
from lib.scoring.engine import ScoringEngine


class TestComputeWeightedScore:
    def test_returns_float_in_range(self, scoring_engine, sample_score_breakdown):
        score = scoring_engine.compute_weighted_score(sample_score_breakdown)
        assert isinstance(score, float)
        assert 1.0 <= score <= 5.0

    def test_all_max_scores(self, scoring_engine):
        sb = ScoreBreakdown(
            comprehensibility=5.0, task_completion=5.0, grammar=5.0,
            naturalness=5.0, politeness_register=5.0, recovery=5.0,
            confidence_hesitation=5.0,
        )
        assert scoring_engine.compute_weighted_score(sb) == pytest.approx(5.0)

    def test_all_min_scores(self, scoring_engine):
        sb = ScoreBreakdown(
            comprehensibility=1.0, task_completion=1.0, grammar=1.0,
            naturalness=1.0, politeness_register=1.0, recovery=1.0,
            confidence_hesitation=1.0,
        )
        assert scoring_engine.compute_weighted_score(sb) == pytest.approx(1.0)


class TestGetRatingLabel:
    def test_needs_practice(self):
        assert ScoringEngine.get_rating_label(1.0) == "Needs Practice"
        assert ScoringEngine.get_rating_label(1.9) == "Needs Practice"

    def test_developing(self):
        assert ScoringEngine.get_rating_label(2.0) == "Developing"
        assert ScoringEngine.get_rating_label(2.9) == "Developing"

    def test_functional(self):
        assert ScoringEngine.get_rating_label(3.0) == "Functional"
        assert ScoringEngine.get_rating_label(3.9) == "Functional"

    def test_strong(self):
        assert ScoringEngine.get_rating_label(4.0) == "Strong"
        assert ScoringEngine.get_rating_label(5.0) == "Strong"


class TestComputeTrend:
    def test_improving(self):
        scores = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
        assert ScoringEngine.compute_trend(scores) == "improving"

    def test_stable(self):
        scores = [3.0, 3.1, 3.0, 3.1, 3.0, 3.1]
        assert ScoringEngine.compute_trend(scores) == "stable"

    def test_declining(self):
        scores = [4.5, 4.0, 3.5, 3.0, 2.5, 2.0]
        assert ScoringEngine.compute_trend(scores) == "declining"

    def test_single_score_returns_stable(self):
        assert ScoringEngine.compute_trend([3.0]) == "stable"

    def test_empty_returns_stable(self):
        assert ScoringEngine.compute_trend([]) == "stable"


class TestIdentifyWeakestDimensions:
    def test_returns_correct_dimensions(self, scoring_engine, sample_score_breakdown):
        weakest = scoring_engine.identify_weakest_dimensions(sample_score_breakdown)
        assert len(weakest) == 3
        # naturalness=2.5 should be the weakest
        assert weakest[0] == "naturalness"

    def test_with_n_parameter(self, scoring_engine, sample_score_breakdown):
        weakest = scoring_engine.identify_weakest_dimensions(sample_score_breakdown, n=2)
        assert len(weakest) == 2

    def test_n_equals_one(self, scoring_engine, sample_score_breakdown):
        weakest = scoring_engine.identify_weakest_dimensions(sample_score_breakdown, n=1)
        assert len(weakest) == 1
        assert weakest[0] == "naturalness"


class TestShouldIncreaseDifficulty:
    def test_high_scores_returns_true(self, scoring_engine):
        high_scores = [
            ScoreBreakdown(
                comprehensibility=4.5, task_completion=4.5, grammar=4.5,
                naturalness=4.5, politeness_register=4.5, recovery=4.5,
                confidence_hesitation=4.5,
            )
        ]
        assert scoring_engine.should_increase_difficulty(high_scores) is True

    def test_low_scores_returns_false(self, scoring_engine):
        low_scores = [
            ScoreBreakdown(
                comprehensibility=2.0, task_completion=2.0, grammar=2.0,
                naturalness=2.0, politeness_register=2.0, recovery=2.0,
                confidence_hesitation=2.0,
            )
        ]
        assert scoring_engine.should_increase_difficulty(low_scores) is False

    def test_empty_list_returns_false(self, scoring_engine):
        assert scoring_engine.should_increase_difficulty([]) is False


class TestShouldDecreaseDifficulty:
    def test_low_scores_returns_true(self, scoring_engine):
        low_scores = [
            ScoreBreakdown(
                comprehensibility=1.5, task_completion=1.5, grammar=1.5,
                naturalness=1.5, politeness_register=1.5, recovery=1.5,
                confidence_hesitation=1.5,
            )
        ]
        assert scoring_engine.should_decrease_difficulty(low_scores) is True

    def test_high_scores_returns_false(self, scoring_engine):
        high_scores = [
            ScoreBreakdown(
                comprehensibility=4.0, task_completion=4.0, grammar=4.0,
                naturalness=4.0, politeness_register=4.0, recovery=4.0,
                confidence_hesitation=4.0,
            )
        ]
        assert scoring_engine.should_decrease_difficulty(high_scores) is False

    def test_empty_list_returns_false(self, scoring_engine):
        assert scoring_engine.should_decrease_difficulty([]) is False


class TestGenerateScoreSummary:
    def test_structure(self, scoring_engine, sample_score_breakdown):
        summary = scoring_engine.generate_score_summary(sample_score_breakdown)
        assert "weighted_score" in summary
        assert "rating" in summary
        assert "weakest_dimensions" in summary
        assert "strongest_dimensions" in summary
        assert isinstance(summary["weighted_score"], float)
        assert isinstance(summary["rating"], str)
        assert len(summary["weakest_dimensions"]) == 3
        assert len(summary["strongest_dimensions"]) == 3
