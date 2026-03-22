"""Learner loop – ties together session management and agent interactions."""

from __future__ import annotations

from typing import Dict, List, Optional

from lib.db.models import Language, ScoreBreakdown, SessionMode
from lib.orchestration.session_manager import SessionManager


class LearnerLoop:
    """Implements the core learner loop for the Travel Language Coach.

    The learner loop follows this flow:
    1. Select profile (Caleb / Wife / Couple)
    2. Select language (French / Italian)
    3. Select mode (Live Mission / Repair Drill / Phrase Coach / Review)
    4. Load learner profile and recent weaknesses
    5. Select scenario based on weaknesses
    6. Load phrase pack
    7. Run conversation (via tutor agent)
    8. Evaluate transcript
    9. Update memory
    10. Return recap with next drill recommendation
    """

    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager
        self._mission_contexts: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Practice lifecycle
    # ------------------------------------------------------------------

    def start_practice(
        self,
        learner_id: str,
        language: Language,
        mode: SessionMode,
        partner_id: Optional[str] = None,
    ) -> dict:
        """Start a new practice session.

        Returns
        -------
        dict
            Contains ``session_id``, ``scenario``, ``language``, ``mode``,
            and ``phrase_pack``.
        """
        session = self.session_manager.create_session(
            learner_id=learner_id,
            language=language,
            mode=mode,
            partner_id=partner_id,
        )

        # Build a profile dict for the tutor
        profile = self.session_manager.memory_agent.get_learner_profile(
            learner_id
        )
        if profile is None:
            from lib.db.models import LearnerProfile

            profile = LearnerProfile(
                learner_id=learner_id,
                name=learner_id,
                target_languages=[language],
            )

        # Load phrase pack for the scenario category
        sm = self.session_manager
        scenario_obj = None
        category = "restaurant"
        if session.scenario_id:
            # Try to find the full scenario object from the agent's registry
            for s in sm.scenario_agent._scenarios:
                if s.scenario_id == session.scenario_id:
                    scenario_obj = s
                    category = s.category.value
                    break

        phrase_result = sm.phrase_retrieval_agent.process({
            "action": "load",
            "language": language.value,
            "category": category,
        })
        phrase_pack = phrase_result.get("phrase_pack", {})

        # Start the tutor mission
        opening = ""
        if scenario_obj:
            tutor_result = sm.tutor_agent.start_mission(
                scenario=scenario_obj,
                learner_profile=profile,
                phrase_pack=phrase_pack,
            )
            opening = tutor_result.get("opening_line", "")
            # Store mission context for later use
            self._mission_contexts[session.session_id] = tutor_result.get(
                "mission_context", {}
            )

        if opening:
            sm.add_to_transcript(session.session_id, "tutor", opening)

        return {
            "session_id": session.session_id,
            "scenario": {
                "scenario_id": session.scenario_id,
                "opening": opening,
            },
            "language": language.value,
            "mode": mode.value,
            "phrase_pack": phrase_pack,
        }

    def submit_learner_input(self, session_id: str, text: str) -> dict:
        """Process learner input during an active session.

        Returns
        -------
        dict
            Contains ``tutor_response``, ``help_offered`` (bool), and
            ``repair_prompted`` (bool).
        """
        self.session_manager.add_to_transcript(session_id, "learner", text)

        session = self.session_manager.get_session(session_id)
        if session is None:
            raise KeyError(f"No session found with id: {session_id}")

        sm = self.session_manager
        context = self._mission_contexts.get(session_id, {})

        # Check whether help is needed
        help_offered = sm.tutor_agent.should_offer_help(
            text, context.get("attempt_count", 1)
        )

        # Decide between a repair prompt or normal response
        repair_prompted = False
        if help_offered:
            tutor_response = sm.tutor_agent.generate_repair_prompt(text)
            repair_prompted = True
        else:
            result = sm.tutor_agent.generate_response(text, context)
            tutor_response = result.get("response", "")
            # Update stored context
            if "context" in result:
                self._mission_contexts[session_id] = result["context"]

        if tutor_response:
            self.session_manager.add_to_transcript(
                session_id, "tutor", tutor_response
            )

        return {
            "tutor_response": tutor_response,
            "help_offered": help_offered,
            "repair_prompted": repair_prompted,
        }

    def end_practice(self, session_id: str) -> dict:
        """End an active practice session and return a full recap."""
        return self.session_manager.end_session(session_id)

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    def get_progress_summary(self, learner_id: str) -> dict:
        """Return an overall progress summary for a learner.

        Returns
        -------
        dict
            Contains ``total_sessions``, ``avg_score``, ``weak_areas``,
            ``strong_areas``, ``recent_trend``, and ``recommended_mode``.
        """
        history = self.session_manager.memory_agent.get_learner_history(
            learner_id
        )
        recent_sessions = history.get("recent_sessions", [])
        total_sessions = history.get("total_sessions", 0)
        avg_score = history.get("average_score", 0.0)

        # Compute trend from recent session scores
        recent_scores = [s["score_avg"] for s in recent_sessions]
        scoring = self.session_manager.scoring_engine
        trend = scoring.compute_trend(recent_scores)

        # Determine weak / strong areas from the latest session's breakdown
        learner_sessions = self.session_manager.get_learner_sessions(
            learner_id
        )
        weak_areas: List[str] = []
        strong_areas: List[str] = []

        scored_sessions = [
            s for s in learner_sessions if s.score_breakdown is not None
        ]
        if scored_sessions:
            latest = scored_sessions[-1]
            if latest.score_breakdown is not None:
                breakdown = ScoreBreakdown(**latest.score_breakdown)
                weak_areas = scoring.identify_weakest_dimensions(breakdown)
                strong_areas = scoring.identify_strongest_dimensions(breakdown)

        # Recommend a mode based on performance
        recommended_mode = self._recommend_mode(avg_score, weak_areas)

        return {
            "total_sessions": total_sessions,
            "avg_score": avg_score,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "recent_trend": trend,
            "recommended_mode": recommended_mode,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _recommend_mode(avg_score: float, weak_areas: List[str]) -> str:
        """Suggest a session mode based on score and weaknesses."""
        if avg_score == 0.0:
            return SessionMode.PHRASE_COACH.value

        if avg_score < 2.0:
            return SessionMode.PHRASE_COACH.value

        grammar_related = {"grammar", "naturalness", "politeness_register"}
        if set(weak_areas) & grammar_related:
            return SessionMode.REPAIR_DRILL.value

        if avg_score < 3.5:
            return SessionMode.LIVE_MISSION.value

        return SessionMode.REVIEW.value
