"""Session manager – manages the complete session lifecycle."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.evaluator.agent import EvaluatorAgent
from agents.memory.agent import MemoryAgent
from agents.phrase_retrieval.agent import PhraseRetrievalAgent
from agents.scenario.agent import ScenarioAgent
from agents.tutor.agent import TutorAgent
from lib.db.models import (
    Language,
    Mistake,
    ScoreBreakdown,
    Session,
    SessionMode,
)
from lib.scoring.engine import ScoringEngine


class SessionManager:
    """Manages the complete session lifecycle for the Travel Language Coach.

    Coordinates agent interactions for session creation, transcript
    management, evaluation, and recap generation.
    """

    def __init__(
        self,
        memory_agent: MemoryAgent,
        scenario_agent: ScenarioAgent,
        phrase_retrieval_agent: PhraseRetrievalAgent,
        tutor_agent: TutorAgent,
        evaluator_agent: EvaluatorAgent,
        scoring_engine: ScoringEngine,
    ) -> None:
        self.memory_agent = memory_agent
        self.scenario_agent = scenario_agent
        self.phrase_retrieval_agent = phrase_retrieval_agent
        self.tutor_agent = tutor_agent
        self.evaluator_agent = evaluator_agent
        self.scoring_engine = scoring_engine

        self._sessions: Dict[str, Session] = {}

    # ------------------------------------------------------------------
    # Session creation
    # ------------------------------------------------------------------

    def create_session(
        self,
        learner_id: str,
        language: Language,
        mode: SessionMode,
        partner_id: Optional[str] = None,
    ) -> Session:
        """Create a new session, load profile, select scenario, and load phrases.

        Parameters
        ----------
        learner_id:
            Primary learner identifier.
        language:
            Target language for the session.
        mode:
            Coaching mode to use.
        partner_id:
            Optional second learner for couple missions.

        Returns
        -------
        Session
            The newly created session object.
        """
        learner_ids = [learner_id]
        if partner_id:
            learner_ids.append(partner_id)

        # Load learner profile via memory agent
        profile = self.memory_agent.get_learner_profile(learner_id)
        if profile is None:
            from lib.db.models import LearnerProfile

            profile = LearnerProfile(
                learner_id=learner_id,
                name=learner_id,
                target_languages=[language],
            )

        # Select a scenario using the direct API (avoids process dispatch)
        scenario = self.scenario_agent.select_scenario(
            learner_profile=profile,
            language=language,
            mode=mode,
        )
        scenario_id = scenario.scenario_id if scenario else None
        category = scenario.category.value if scenario else "restaurant"

        # Load phrase pack for the scenario category
        self.phrase_retrieval_agent.process({
            "action": "load",
            "language": language.value,
            "category": category,
        })

        # Build the session
        session = Session(
            mode=mode,
            language=language,
            learner_ids=learner_ids,
            scenario_id=scenario_id,
        )
        self._sessions[session.session_id] = session
        return session

    # ------------------------------------------------------------------
    # Transcript management
    # ------------------------------------------------------------------

    def add_to_transcript(
        self, session_id: str, role: str, content: str
    ) -> None:
        """Append a message to the session transcript.

        Parameters
        ----------
        session_id:
            Identifier of the active session.
        role:
            Speaker role (e.g. ``"learner"``, ``"tutor"``).
        content:
            The message text.

        Raises
        ------
        KeyError
            If *session_id* does not match an active session.
        """
        session = self._get_or_raise(session_id)
        session.transcript.append({"role": role, "content": content})

    # ------------------------------------------------------------------
    # Session retrieval
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its ID, or ``None`` if not found."""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[Session]:
        """Return all sessions that have not been scored (i.e. still active)."""
        return [
            s for s in self._sessions.values() if s.score_breakdown is None
        ]

    def get_learner_sessions(self, learner_id: str) -> List[Session]:
        """Return every session that includes *learner_id*."""
        return [
            s
            for s in self._sessions.values()
            if learner_id in s.learner_ids
        ]

    # ------------------------------------------------------------------
    # Session completion
    # ------------------------------------------------------------------

    def end_session(self, session_id: str) -> dict:
        """End a session: evaluate, score, update memory, and return a recap.

        Returns
        -------
        dict
            Recap dictionary with keys: ``session_id``, ``score_breakdown``,
            ``mistakes``, ``recap_text``, ``next_drill``, ``rating``.

        Raises
        ------
        KeyError
            If *session_id* does not match an active session.
        """
        session = self._get_or_raise(session_id)

        # Evaluate the transcript
        score, mistakes = self.evaluator_agent.evaluate_session(session)

        # Compute scoring summary
        summary = self.scoring_engine.generate_score_summary(score)

        # Generate recap text
        recap_text = self.evaluator_agent.generate_recap(
            session, score, mistakes
        )

        # Recommend next drill
        learner_id = session.learner_ids[0]
        profile = self.memory_agent.get_learner_profile(learner_id)
        if profile is None:
            from lib.db.models import LearnerProfile

            profile = LearnerProfile(
                learner_id=learner_id,
                name=learner_id,
                target_languages=[session.language],
            )
        next_drill = self.evaluator_agent.recommend_next_drill(
            score, mistakes, profile
        )

        # Persist score on the session
        session.score_breakdown = self.scoring_engine.breakdown_to_dict(score)
        session.summary = recap_text
        session.next_drill = next_drill

        # Update memory
        self.memory_agent.update_after_session(session, score, mistakes)

        return {
            "session_id": session_id,
            "score_breakdown": summary,
            "mistakes": [m.model_dump() for m in mistakes],
            "recap_text": recap_text,
            "next_drill": next_drill,
            "rating": summary["rating"],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_raise(self, session_id: str) -> Session:
        """Return the session or raise :class:`KeyError`."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"No session found with id: {session_id}")
        return session
