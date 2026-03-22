"""Evaluator Agent – scores sessions, extracts mistakes, and generates recaps."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from lib.db.models import (
    CorrectionLabel,
    DifficultyLevel,
    LearnerProfile,
    Mistake,
    MistakeSeverity,
    MistakeType,
    ScoreBreakdown,
    Session,
)


class EvaluatorAgent(BaseAgent):
    """Analyses a completed session transcript to produce scores, classify
    mistakes, generate a learning recap, and recommend the next drill.
    """

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "evaluator"

    @property
    def agent_role(self) -> str:
        return (
            "Evaluate completed sessions by scoring the learner's performance, "
            "extracting and classifying mistakes, producing a concise recap, "
            "and recommending the next practice focus."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate evaluator method based on *action*.

        Supported actions: ``evaluate``, ``extract_mistakes``, ``recap``,
        ``recommend``.
        """
        action = payload.get("action")
        if action == "evaluate":
            session = self._to_session(payload["session"])
            score, mistakes = self.evaluate_session(session)
            return {
                "score": score.model_dump(),
                "mistakes": [m.model_dump() for m in mistakes],
            }
        if action == "extract_mistakes":
            return {
                "mistakes": [
                    m.model_dump()
                    for m in self.extract_mistakes(
                        payload["transcript"], payload["language"]
                    )
                ]
            }
        if action == "recap":
            session = self._to_session(payload["session"])
            score = ScoreBreakdown(**payload["score"])
            mistakes = [Mistake(**m) for m in payload["mistakes"]]
            return {"recap": self.generate_recap(session, score, mistakes)}
        if action == "recommend":
            score = ScoreBreakdown(**payload["score"])
            mistakes = [Mistake(**m) for m in payload["mistakes"]]
            profile = LearnerProfile(**payload["learner_profile"])
            return {"next_drill": self.recommend_next_drill(score, mistakes, profile)}
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are the Evaluator for a Travel Language Coach. After each session "
            "you receive the full transcript and must:\n"
            "1. Score the learner on 7 dimensions (1-5 each): comprehensibility, "
            "task_completion, grammar, naturalness, politeness_register, recovery, "
            "confidence_hesitation.\n"
            "2. Extract every mistake and classify it with a CorrectionLabel: "
            "correct, understandable_but_unnatural, incorrect, too_formal, too_blunt, "
            "or uncommon_wording.\n"
            "3. Assign each mistake a MistakeType (grammar, vocabulary, pronunciation, "
            "register, naturalness, comprehension) and severity (low, medium, high).\n"
            "4. Produce a concise, encouraging recap highlighting strengths and "
            "1-2 areas to improve.\n"
            "5. Recommend the single most impactful next drill based on the score "
            "breakdown and recurring mistakes."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_session(
        self, session: Session
    ) -> tuple[ScoreBreakdown, List[Mistake]]:
        """Score *session* and extract mistakes.

        Parameters
        ----------
        session:
            A completed :class:`Session` with a populated transcript.

        Returns
        -------
        tuple[ScoreBreakdown, list[Mistake]]
            The score breakdown and list of detected mistakes.
        """
        mistakes = self.extract_mistakes(
            session.transcript, session.language.value
        )
        score = self._compute_score(session.transcript, mistakes)
        return score, mistakes

    def extract_mistakes(
        self, transcript: List[Dict[str, str]], language: str
    ) -> List[Mistake]:
        """Parse *transcript* and return a list of :class:`Mistake` objects.

        In a full implementation this would call an LLM.  The placeholder
        delegates to ``_call_llm`` and returns an empty list (no real
        parsing without a model).
        """
        self._call_llm(
            self.get_system_prompt(),
            (
                f"Analyse the following {language} transcript and extract all "
                f"mistakes:\n{transcript}"
            ),
        )
        # Without a real LLM we cannot parse mistakes; return empty.
        return []

    def generate_recap(
        self,
        session: Session,
        score: ScoreBreakdown,
        mistakes: List[Mistake],
    ) -> str:
        """Produce a concise learning recap string.

        Parameters
        ----------
        session:
            The completed session.
        score:
            The computed score breakdown.
        mistakes:
            List of extracted mistakes.

        Returns
        -------
        str
            A short, encouraging recap suitable for the learner.
        """
        mistake_summary = ", ".join(
            f"{m.type.value}: '{m.source_phrase}'" for m in mistakes
        ) or "No mistakes detected"
        recap = self._call_llm(
            self.get_system_prompt(),
            (
                f"Session {session.session_id} recap:\n"
                f"Overall rating: {score.overall_rating} "
                f"(weighted avg {score.weighted_average:.2f})\n"
                f"Mistakes: {mistake_summary}\n"
                "Write an encouraging 2-3 sentence recap."
            ),
        )
        return recap

    def recommend_next_drill(
        self,
        score: ScoreBreakdown,
        mistakes: List[Mistake],
        learner_profile: LearnerProfile,
    ) -> str:
        """Suggest the single most impactful next practice focus.

        The recommendation is based on the weakest scoring dimension and
        the most frequent mistake type.
        """
        weakest = self._weakest_dimension(score)
        frequent_type = self._most_frequent_mistake_type(mistakes)

        recommendation = self._call_llm(
            self.get_system_prompt(),
            (
                f"Weakest dimension: {weakest}, most frequent mistake type: "
                f"{frequent_type}. Recommend the next drill for a "
                f"{learner_profile.name}."
            ),
        )
        return recommendation

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_score(
        transcript: List[Dict[str, str]], mistakes: List[Mistake]
    ) -> ScoreBreakdown:
        """Compute a heuristic :class:`ScoreBreakdown`.

        Without an LLM, scores are derived from simple heuristics:
        * Longer transcripts suggest higher task completion.
        * Fewer mistakes raise grammar / naturalness scores.
        """
        learner_turns = [
            t for t in transcript if t.get("role") == "learner"
        ]
        turn_count = max(len(learner_turns), 1)
        mistake_count = len(mistakes)

        base = min(3.0 + turn_count * 0.2, 5.0)
        penalty = min(mistake_count * 0.3, 2.0)

        def _clamp(val: float) -> float:
            return max(1.0, min(val, 5.0))

        return ScoreBreakdown(
            comprehensibility=_clamp(base - penalty * 0.5),
            task_completion=_clamp(base),
            grammar=_clamp(base - penalty),
            naturalness=_clamp(base - penalty * 0.7),
            politeness_register=_clamp(base - penalty * 0.3),
            recovery=_clamp(base - penalty * 0.2),
            confidence_hesitation=_clamp(base - penalty * 0.4),
        )

    @staticmethod
    def _weakest_dimension(score: ScoreBreakdown) -> str:
        """Return the name of the lowest-scoring dimension."""
        dimensions = {
            "comprehensibility": score.comprehensibility,
            "task_completion": score.task_completion,
            "grammar": score.grammar,
            "naturalness": score.naturalness,
            "politeness_register": score.politeness_register,
            "recovery": score.recovery,
            "confidence_hesitation": score.confidence_hesitation,
        }
        return min(dimensions, key=dimensions.get)  # type: ignore[arg-type]

    @staticmethod
    def _most_frequent_mistake_type(mistakes: List[Mistake]) -> str:
        """Return the most frequent :class:`MistakeType` as a string."""
        if not mistakes:
            return "none"
        counts: Dict[str, int] = {}
        for m in mistakes:
            counts[m.type.value] = counts.get(m.type.value, 0) + 1
        return max(counts, key=counts.get)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_session(data: Any) -> Session:
        if isinstance(data, dict):
            return Session(**data)
        return data
