"""Scoring engine for travel language practice sessions."""

from __future__ import annotations

from typing import Dict, List

from lib.db.models import ScoreBreakdown


class ScoringEngine:
    """Computes and manages scoring for travel language practice sessions."""

    WEIGHTS: Dict[str, float] = {
        "comprehensibility": 0.20,
        "task_completion": 0.20,
        "recovery": 0.15,
        "confidence_hesitation": 0.15,
        "grammar": 0.10,
        "naturalness": 0.10,
        "politeness_register": 0.10,
    }

    # ------------------------------------------------------------------
    # Score computation
    # ------------------------------------------------------------------

    def compute_weighted_score(self, score_breakdown: ScoreBreakdown) -> float:
        """Compute the weighted average across all scoring dimensions."""
        dimensions = self.breakdown_to_dict(score_breakdown)
        return sum(
            dimensions[dim] * weight for dim, weight in self.WEIGHTS.items()
        )

    @staticmethod
    def get_rating_label(score: float) -> str:
        """Return a human-readable rating for a numeric score.

        Ranges (inclusive lower, exclusive upper except the last):
            1-2: "Needs Practice"
            2-3: "Developing"
            3-4: "Functional"
            4-5: "Strong"
        """
        if score < 2.0:
            return "Needs Practice"
        if score < 3.0:
            return "Developing"
        if score < 4.0:
            return "Functional"
        return "Strong"

    @staticmethod
    def compute_trend(scores: List[float]) -> str:
        """Determine whether recent scores are improving, stable, or declining.

        Uses a simple comparison of the mean of the first half vs. the
        second half of the provided scores list.
        """
        if len(scores) < 2:
            return "stable"

        mid = len(scores) // 2
        first_half = scores[:mid]
        second_half = scores[mid:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        delta = avg_second - avg_first
        if delta > 0.25:
            return "improving"
        if delta < -0.25:
            return "declining"
        return "stable"

    def identify_weakest_dimensions(
        self, score_breakdown: ScoreBreakdown, n: int = 3
    ) -> List[str]:
        """Return the *n* lowest-scoring dimension names."""
        dimensions = self.breakdown_to_dict(score_breakdown)
        ranked = sorted(dimensions, key=lambda d: dimensions[d])
        return ranked[:n]

    def identify_strongest_dimensions(
        self, score_breakdown: ScoreBreakdown, n: int = 3
    ) -> List[str]:
        """Return the *n* highest-scoring dimension names."""
        dimensions = self.breakdown_to_dict(score_breakdown)
        ranked = sorted(dimensions, key=lambda d: dimensions[d], reverse=True)
        return ranked[:n]

    # ------------------------------------------------------------------
    # Difficulty recommendations
    # ------------------------------------------------------------------

    def should_increase_difficulty(
        self,
        recent_scores: List[ScoreBreakdown],
        threshold: float = 3.5,
    ) -> bool:
        """Suggest increasing difficulty when the average weighted score
        of recent sessions exceeds *threshold*.
        """
        if not recent_scores:
            return False
        avg = sum(
            self.compute_weighted_score(s) for s in recent_scores
        ) / len(recent_scores)
        return avg > threshold

    def should_decrease_difficulty(
        self,
        recent_scores: List[ScoreBreakdown],
        threshold: float = 2.0,
    ) -> bool:
        """Suggest decreasing difficulty when the average weighted score
        of recent sessions falls below *threshold*.
        """
        if not recent_scores:
            return False
        avg = sum(
            self.compute_weighted_score(s) for s in recent_scores
        ) / len(recent_scores)
        return avg < threshold

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def generate_score_summary(self, score_breakdown: ScoreBreakdown) -> dict:
        """Return a summary dict with score, rating, and top dimensions."""
        weighted = self.compute_weighted_score(score_breakdown)
        return {
            "weighted_score": round(weighted, 2),
            "rating": self.get_rating_label(weighted),
            "weakest_dimensions": self.identify_weakest_dimensions(
                score_breakdown
            ),
            "strongest_dimensions": self.identify_strongest_dimensions(
                score_breakdown
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def breakdown_to_dict(score_breakdown: ScoreBreakdown) -> Dict[str, float]:
        """Convert a :class:`ScoreBreakdown` to a plain dict of dimension scores."""
        return {
            "comprehensibility": score_breakdown.comprehensibility,
            "task_completion": score_breakdown.task_completion,
            "recovery": score_breakdown.recovery,
            "confidence_hesitation": score_breakdown.confidence_hesitation,
            "grammar": score_breakdown.grammar,
            "naturalness": score_breakdown.naturalness,
            "politeness_register": score_breakdown.politeness_register,
        }
