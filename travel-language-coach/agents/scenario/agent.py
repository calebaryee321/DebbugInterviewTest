"""Scenario Agent – selects and manages practice scenarios for missions."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from lib.db.models import (
    DifficultyLevel,
    Language,
    LearnerProfile,
    Scenario,
    ScenarioCategory,
    SessionMode,
)

# Ordered levels for arithmetic on difficulty.
_DIFFICULTY_ORDER: List[DifficultyLevel] = [
    DifficultyLevel.BEGINNER,
    DifficultyLevel.ELEMENTARY,
    DifficultyLevel.INTERMEDIATE,
    DifficultyLevel.UPPER_INTERMEDIATE,
    DifficultyLevel.ADVANCED,
]


class ScenarioAgent(BaseAgent):
    """Manages a registry of :class:`Scenario` objects and selects the best
    next scenario for a learner based on their weaknesses, difficulty level,
    and recent history.
    """

    def __init__(self, scenarios: List[Scenario] | None = None) -> None:
        """Initialise the agent with an optional list of scenarios.

        Parameters
        ----------
        scenarios:
            Pre-loaded scenario objects.  Pass ``None`` or ``[]`` and add
            scenarios later via the registry.
        """
        self._scenarios: List[Scenario] = list(scenarios) if scenarios else []

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "scenario"

    @property
    def agent_role(self) -> str:
        return (
            "Select and manage practice scenarios based on learner weaknesses, "
            "difficulty progression, and recent session history."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate scenario method based on *action*.

        Supported actions: ``select``, ``adjust_difficulty``,
        ``by_category``, ``by_difficulty``.
        """
        action = payload.get("action")
        if action == "select":
            profile = LearnerProfile(**payload["learner_profile"])
            language = Language(payload["language"])
            mode = SessionMode(payload["mode"])
            recent = payload.get("recent_scenarios")
            scenario = self.select_scenario(profile, language, mode, recent)
            return {"scenario": scenario.model_dump() if scenario else None}
        if action == "adjust_difficulty":
            new_diff = self.adjust_difficulty(
                DifficultyLevel(payload["current_difficulty"]),
                payload["score"],
            )
            return {"new_difficulty": new_diff.value}
        if action == "by_category":
            cat = ScenarioCategory(payload["category"])
            lang = Language(payload["language"])
            return {
                "scenarios": [
                    s.model_dump()
                    for s in self.get_scenarios_by_category(cat, lang)
                ]
            }
        if action == "by_difficulty":
            diff = DifficultyLevel(payload["difficulty"])
            lang = Language(payload["language"])
            return {
                "scenarios": [
                    s.model_dump()
                    for s in self.get_scenarios_by_difficulty(diff, lang)
                ]
            }
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are the Scenario Agent for a Travel Language Coach. Your job is to "
            "choose the best next practice scenario for the learner. Follow these rules:\n"
            "1. Prioritise scenarios that target the learner's weak categories.\n"
            "2. Avoid scenarios the learner has recently completed to keep practice fresh.\n"
            "3. Adjust difficulty based on recent performance – step up after strong "
            "sessions, step down after struggling ones.\n"
            "4. If no weak scenarios are available, pick from untried or least-recently "
            "attempted categories.\n"
            "5. For couple missions, choose scenarios that encourage collaboration and "
            "turn-taking between the two learners."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_scenario(
        self,
        learner_profile: LearnerProfile,
        language: Language,
        mode: SessionMode,
        recent_scenarios: Optional[List[str]] = None,
    ) -> Optional[Scenario]:
        """Pick the next scenario for the learner.

        Selection priority:
        1. Scenarios matching the learner's ``weak_scenarios``.
        2. Scenarios **not** in *recent_scenarios*.
        3. Difficulty-appropriate scenarios.
        4. Random fallback among remaining candidates.

        Returns ``None`` if the registry is empty for *language*.
        """
        recent_scenarios = recent_scenarios or []
        candidates = [s for s in self._scenarios if s.language == language]
        if not candidates:
            return None

        target_difficulty = self._target_difficulty(learner_profile, language)

        # 1. Prefer weak-scenario categories
        weak_cats = set(learner_profile.weak_scenarios)
        weak_matches = [
            s
            for s in candidates
            if s.category.value in weak_cats
            and s.scenario_id not in recent_scenarios
        ]
        if weak_matches:
            level_matches = [
                s for s in weak_matches if s.difficulty == target_difficulty
            ]
            return random.choice(level_matches) if level_matches else random.choice(weak_matches)

        # 2. Exclude recently completed
        not_recent = [
            s for s in candidates if s.scenario_id not in recent_scenarios
        ]
        pool = not_recent if not_recent else candidates

        # 3. Prefer matching difficulty
        level_matches = [s for s in pool if s.difficulty == target_difficulty]
        if level_matches:
            return random.choice(level_matches)

        return random.choice(pool)

    def adjust_difficulty(
        self, current_difficulty: DifficultyLevel, score: float
    ) -> DifficultyLevel:
        """Return a new difficulty level based on *score* (weighted avg 1-5).

        * score ≥ 4.0 → step up
        * score < 2.5 → step down
        * otherwise → stay
        """
        idx = _DIFFICULTY_ORDER.index(current_difficulty)
        if score >= 4.0 and idx < len(_DIFFICULTY_ORDER) - 1:
            return _DIFFICULTY_ORDER[idx + 1]
        if score < 2.5 and idx > 0:
            return _DIFFICULTY_ORDER[idx - 1]
        return current_difficulty

    def get_scenarios_by_category(
        self, category: ScenarioCategory, language: Language
    ) -> List[Scenario]:
        """Return all scenarios matching *category* and *language*."""
        return [
            s
            for s in self._scenarios
            if s.category == category and s.language == language
        ]

    def get_scenarios_by_difficulty(
        self, difficulty: DifficultyLevel, language: Language
    ) -> List[Scenario]:
        """Return all scenarios matching *difficulty* and *language*."""
        return [
            s
            for s in self._scenarios
            if s.difficulty == difficulty and s.language == language
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _target_difficulty(
        profile: LearnerProfile, language: Language
    ) -> DifficultyLevel:
        """Determine the appropriate difficulty from the learner's profile."""
        if language == Language.FRENCH:
            return profile.estimated_french_level
        if language == Language.ITALIAN:
            return profile.estimated_italian_level
        return DifficultyLevel.BEGINNER
