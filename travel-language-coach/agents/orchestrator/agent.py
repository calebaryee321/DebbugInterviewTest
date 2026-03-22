"""Orchestrator Agent – coordinates sessions and routes work to other agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agents.base import BaseAgent
from lib.db.models import (
    DifficultyLevel,
    Language,
    LearnerProfile,
    Session,
    SessionMode,
)


class OrchestratorAgent(BaseAgent):
    """Central coordinator that starts sessions, loads learner context,
    routes work to the appropriate agents, and finalises session recaps.
    """

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "orchestrator"

    @property
    def agent_role(self) -> str:
        return (
            "Coordinate the coaching session lifecycle: determine active mode, "
            "load learner memory, choose which agents to invoke, and manage "
            "session state from start to recap."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate orchestrator method based on *action*.

        Supported actions: ``start_session``, ``load_context``,
        ``route``, ``end_session``.
        """
        action = payload.get("action")
        if action == "start_session":
            return self.start_session(
                learner_id=payload["learner_id"],
                language=payload["language"],
                mode=payload["mode"],
                couple_mode=payload.get("couple_mode", False),
            )
        if action == "load_context":
            return self.load_learner_context(payload["learner_id"])
        if action == "route":
            return self.route_to_agents(payload["session_config"])
        if action == "end_session":
            return self.end_session(payload["session_id"])
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are the Orchestrator of a Travel Language Coach. "
            "Your job is to manage the full lifecycle of a coaching session. "
            "You determine whether the learner is practising solo or as a couple, "
            "load their profile and learning history, decide which specialist agents "
            "(Tutor, Evaluator, Scenario, Phrase Retrieval, Memory) to invoke, and "
            "ensure smooth handoffs between them. At the end of each session you "
            "compile a concise recap that includes scores, mistakes, and a recommended "
            "next drill. Always prioritise a supportive, encouraging coaching tone."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        learner_id: str,
        language: str | Language,
        mode: str | SessionMode,
        couple_mode: bool = False,
    ) -> Dict[str, Any]:
        """Initialise a new coaching session and return a config dict.

        Parameters
        ----------
        learner_id:
            Primary learner's identifier.
        language:
            Target language for this session.
        mode:
            Desired session mode.
        couple_mode:
            If ``True`` the session is a joint couple mission.

        Returns
        -------
        dict
            Session configuration including IDs, mode flags, and empty
            agent pipeline.
        """
        language = Language(language) if isinstance(language, str) else language
        mode = SessionMode(mode) if isinstance(mode, str) else mode

        if couple_mode:
            mode = SessionMode.COUPLE_MISSION

        session_id = str(uuid4())
        return {
            "session_id": session_id,
            "learner_id": learner_id,
            "language": language.value,
            "mode": mode.value,
            "couple_mode": couple_mode,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active_agents": self._determine_agents(mode),
            "state": "initialized",
        }

    def load_learner_context(self, learner_id: str) -> Dict[str, Any]:
        """Load profile and history for *learner_id*.

        In a full implementation this delegates to the Memory Agent.
        Here it returns a skeleton context dict.
        """
        return {
            "learner_id": learner_id,
            "profile": None,
            "recent_sessions": [],
            "weak_scenarios": [],
            "strong_scenarios": [],
            "common_errors": [],
            "loaded": True,
        }

    def route_to_agents(self, session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Decide which agents to invoke for *session_config* and return the
        ordered pipeline.
        """
        mode = SessionMode(session_config["mode"])
        agents = self._determine_agents(mode)
        return {
            "session_id": session_config.get("session_id"),
            "pipeline": agents,
            "mode": mode.value,
        }

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """Collect outputs from all agents and produce a recap.

        In a full system this aggregates evaluator scores, memory updates,
        and recommended drills.  The placeholder returns a template recap.
        """
        recap = self._call_llm(
            self.get_system_prompt(),
            f"Produce a session recap for session {session_id}.",
        )
        return {
            "session_id": session_id,
            "state": "completed",
            "recap": recap,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_agents(mode: SessionMode) -> List[str]:
        """Return the list of agent names required for *mode*."""
        common: List[str] = ["memory", "phrase_retrieval"]
        if mode == SessionMode.LIVE_MISSION:
            return ["scenario", "tutor", *common, "evaluator"]
        if mode == SessionMode.COUPLE_MISSION:
            return ["scenario", "tutor", *common, "evaluator"]
        if mode == SessionMode.REPAIR_DRILL:
            return ["tutor", *common, "evaluator"]
        if mode == SessionMode.PHRASE_COACH:
            return [*common, "tutor"]
        if mode == SessionMode.REVIEW:
            return [*common, "evaluator"]
        return common
