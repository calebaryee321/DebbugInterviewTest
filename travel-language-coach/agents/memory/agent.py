"""Memory Agent – in-memory store for learner profiles, mistakes, and phrase mastery."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from lib.db.models import (
    CoupleProfile,
    LearnerProfile,
    Mistake,
    PhraseMastery,
    ScoreBreakdown,
    Session,
)


class MemoryAgent(BaseAgent):
    """Manages persistent learner data using in-memory dictionaries.

    Stores learner profiles, couple profiles, mistake history, and phrase
    mastery records.  In production these dicts would be replaced by a
    database or vector store.
    """

    def __init__(self) -> None:
        self._learner_profiles: Dict[str, LearnerProfile] = {}
        self._couple_profiles: Dict[str, CoupleProfile] = {}
        self._mistakes: Dict[str, List[Mistake]] = {}  # learner_id -> list
        self._phrase_mastery: Dict[str, Dict[str, PhraseMastery]] = {}  # learner_id -> {phrase_id -> mastery}
        self._session_history: Dict[str, List[Dict[str, Any]]] = {}  # learner_id -> list of summaries

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "memory"

    @property
    def agent_role(self) -> str:
        return (
            "Persist and retrieve learner profiles, couple profiles, mistake "
            "records, and phrase mastery data across sessions."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate memory method based on *action*.

        Supported actions: ``store_profile``, ``get_profile``,
        ``store_couple``, ``get_couple``, ``record_mistake``,
        ``get_mistakes``, ``update_mastery``, ``get_weak_phrases``,
        ``update_after_session``, ``get_history``.
        """
        action = payload.get("action")
        if action == "store_profile":
            profile = LearnerProfile(**payload["profile"])
            self.store_learner_profile(profile)
            return {"stored": True, "learner_id": profile.learner_id}
        if action == "get_profile":
            p = self.get_learner_profile(payload["learner_id"])
            return {"profile": p.model_dump() if p else None}
        if action == "store_couple":
            cp = CoupleProfile(**payload["profile"])
            self.store_couple_profile(cp)
            return {"stored": True, "couple_id": cp.couple_profile_id}
        if action == "get_couple":
            cp = self.get_couple_profile(payload["couple_id"])
            return {"profile": cp.model_dump() if cp else None}
        if action == "record_mistake":
            m = Mistake(**payload["mistake"])
            self.record_mistake(m)
            return {"recorded": True}
        if action == "get_mistakes":
            ms = self.get_learner_mistakes(
                payload["learner_id"], payload.get("limit", 10)
            )
            return {"mistakes": [m.model_dump() for m in ms]}
        if action == "update_mastery":
            pm = PhraseMastery(**payload["mastery"])
            self.update_phrase_mastery(pm)
            return {"updated": True}
        if action == "get_weak_phrases":
            weak = self.get_weak_phrases(
                payload["learner_id"], payload.get("threshold", 0.5)
            )
            return {"phrases": [p.model_dump() for p in weak]}
        if action == "update_after_session":
            session = Session(**payload["session"])
            score = ScoreBreakdown(**payload["score"])
            mistakes = [Mistake(**m) for m in payload["mistakes"]]
            self.update_after_session(session, score, mistakes)
            return {"updated": True}
        if action == "get_history":
            return self.get_learner_history(payload["learner_id"])
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are the Memory Agent for a Travel Language Coach. You store and "
            "retrieve all persistent learner data including profiles, couple profiles, "
            "mistake histories, and phrase mastery records. When asked to recall "
            "learner context, return the most relevant data concisely. When updating "
            "records, merge new information with existing data rather than overwriting. "
            "Track mistake recurrence counts so the system can identify persistent "
            "weaknesses."
        )

    # ------------------------------------------------------------------
    # Learner profiles
    # ------------------------------------------------------------------

    def store_learner_profile(self, profile: LearnerProfile) -> None:
        """Save or overwrite a :class:`LearnerProfile`."""
        profile.updated_at = datetime.utcnow()
        self._learner_profiles[profile.learner_id] = profile

    def get_learner_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        """Retrieve a learner profile by ID, or ``None`` if not found."""
        return self._learner_profiles.get(learner_id)

    # ------------------------------------------------------------------
    # Couple profiles
    # ------------------------------------------------------------------

    def store_couple_profile(self, profile: CoupleProfile) -> None:
        """Save or overwrite a :class:`CoupleProfile`."""
        profile.updated_at = datetime.utcnow()
        self._couple_profiles[profile.couple_profile_id] = profile

    def get_couple_profile(self, couple_id: str) -> Optional[CoupleProfile]:
        """Retrieve a couple profile by ID, or ``None`` if not found."""
        return self._couple_profiles.get(couple_id)

    # ------------------------------------------------------------------
    # Mistakes
    # ------------------------------------------------------------------

    def record_mistake(self, mistake: Mistake) -> None:
        """Add a mistake, incrementing recurrence if an identical one exists.

        Two mistakes are considered identical when they share the same
        ``learner_id``, ``source_phrase``, and ``type``.
        """
        mistakes = self._mistakes.setdefault(mistake.learner_id, [])
        for existing in mistakes:
            if (
                existing.source_phrase == mistake.source_phrase
                and existing.type == mistake.type
            ):
                existing.recurrence_count += 1
                existing.last_seen = datetime.utcnow()
                return
        self._mistakes[mistake.learner_id].append(mistake)

    def get_learner_mistakes(
        self, learner_id: str, limit: int = 10
    ) -> List[Mistake]:
        """Return the *limit* most recent mistakes for *learner_id*."""
        mistakes = self._mistakes.get(learner_id, [])
        sorted_mistakes = sorted(
            mistakes, key=lambda m: m.last_seen, reverse=True
        )
        return sorted_mistakes[:limit]

    # ------------------------------------------------------------------
    # Phrase mastery
    # ------------------------------------------------------------------

    def update_phrase_mastery(self, mastery: PhraseMastery) -> None:
        """Create or update a :class:`PhraseMastery` record."""
        learner_store = self._phrase_mastery.setdefault(mastery.learner_id, {})
        existing = learner_store.get(mastery.phrase_id)
        if existing:
            existing.familiarity_score = mastery.familiarity_score
            existing.success_under_pressure = mastery.success_under_pressure
            existing.last_practiced = mastery.last_practiced or datetime.utcnow()
            existing.last_failed = mastery.last_failed
            existing.notes = list({*existing.notes, *mastery.notes})
        else:
            learner_store[mastery.phrase_id] = mastery

    def get_weak_phrases(
        self, learner_id: str, threshold: float = 0.5
    ) -> List[PhraseMastery]:
        """Return phrases whose ``familiarity_score`` is below *threshold*."""
        learner_store = self._phrase_mastery.get(learner_id, {})
        return [
            pm
            for pm in learner_store.values()
            if pm.familiarity_score < threshold
        ]

    # ------------------------------------------------------------------
    # Post-session updates
    # ------------------------------------------------------------------

    def update_after_session(
        self,
        session: Session,
        score: ScoreBreakdown,
        mistakes: List[Mistake],
    ) -> None:
        """Update all relevant memory stores after a completed session.

        * Records each mistake (with recurrence tracking).
        * Appends a session summary to the learner's history.
        * Updates the learner profile's weak/strong scenarios if possible.
        """
        for m in mistakes:
            self.record_mistake(m)

        summary = {
            "session_id": session.session_id,
            "mode": session.mode.value,
            "language": session.language.value,
            "score_avg": score.weighted_average,
            "rating": score.overall_rating,
            "mistake_count": len(mistakes),
            "completed_at": datetime.utcnow().isoformat(),
        }
        for lid in session.learner_ids:
            self._session_history.setdefault(lid, []).append(summary)

    # ------------------------------------------------------------------
    # History / stats
    # ------------------------------------------------------------------

    def get_learner_history(self, learner_id: str) -> Dict[str, Any]:
        """Return a summary dict of learner stats."""
        sessions = self._session_history.get(learner_id, [])
        mistakes = self._mistakes.get(learner_id, [])
        weak = self.get_weak_phrases(learner_id)

        avg_score = 0.0
        if sessions:
            avg_score = sum(s["score_avg"] for s in sessions) / len(sessions)

        return {
            "learner_id": learner_id,
            "total_sessions": len(sessions),
            "average_score": round(avg_score, 2),
            "total_mistakes": len(mistakes),
            "recurring_mistakes": sum(
                1 for m in mistakes if m.recurrence_count > 1
            ),
            "weak_phrase_count": len(weak),
            "recent_sessions": sessions[-5:],
        }
