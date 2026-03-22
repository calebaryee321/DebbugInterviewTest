"""Tutor Agent – plays the local persona during missions, coaches the learner."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from lib.db.models import (
    LearnerProfile,
    Scenario,
)

# Attempt threshold after which the tutor offers explicit help.
_MAX_UNAIDED_ATTEMPTS = 2


class TutorAgent(BaseAgent):
    """In-character language tutor that role-plays as a local persona during
    missions, prioritises communication over grammar, and pushes the learner
    to self-repair before revealing answers.
    """

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "tutor"

    @property
    def agent_role(self) -> str:
        return (
            "Role-play as a local persona in the target language during "
            "live missions. Stay in the target language, prioritise "
            "communicative success, push repair before revealing the answer, "
            "and never over-correct during a live exchange."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate tutor method based on *action*.

        Supported actions: ``start_mission``, ``respond``, ``check_help``,
        ``repair``.
        """
        action = payload.get("action")
        if action == "start_mission":
            return self.start_mission(
                scenario=payload["scenario"],
                learner_profile=payload["learner_profile"],
                phrase_pack=payload.get("phrase_pack", []),
            )
        if action == "respond":
            return self.generate_response(
                learner_input=payload["learner_input"],
                context=payload.get("context", {}),
            )
        if action == "check_help":
            return {
                "offer_help": self.should_offer_help(
                    payload["learner_input"],
                    payload.get("attempt_count", 1),
                )
            }
        if action == "repair":
            return {
                "repair_prompt": self.generate_repair_prompt(
                    payload["original_input"]
                )
            }
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are a friendly local in the target country, playing a specific "
            "role (waiter, shopkeeper, hotel clerk, etc.) during a live language "
            "mission. Follow these rules strictly:\n"
            "1. Stay in the TARGET LANGUAGE at all times during the mission.\n"
            "2. Prioritise communicative success – if the learner gets the message "
            "across, keep the conversation moving.\n"
            "3. Do NOT over-correct grammar or vocabulary during the live exchange.\n"
            "4. If the learner struggles, first push them to rephrase (repair) "
            "before revealing the correct form.\n"
            "5. Adapt your speech complexity to the learner's estimated level.\n"
            "6. Be warm, patient, and encouraging. Use culturally appropriate "
            "greetings, fillers, and politeness markers.\n"
            "7. When the learner completes the mission goal, acknowledge it "
            "naturally in character."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_mission(
        self,
        scenario: Scenario | Dict[str, Any],
        learner_profile: LearnerProfile | Dict[str, Any],
        phrase_pack: List[str] | None = None,
    ) -> Dict[str, Any]:
        """Set up the mission context and return the opening line.

        Parameters
        ----------
        scenario:
            The :class:`Scenario` (or dict representation) for this mission.
        learner_profile:
            The learner's profile for level adaptation.
        phrase_pack:
            Optional list of key phrases relevant to the scenario.

        Returns
        -------
        dict
            ``mission_context`` ready for the conversation loop and an
            ``opening_line`` from the local persona.
        """
        if isinstance(scenario, dict):
            scenario = Scenario(**scenario)
        if isinstance(learner_profile, dict):
            learner_profile = LearnerProfile(**learner_profile)

        context = {
            "scenario_id": scenario.scenario_id,
            "category": scenario.category.value,
            "local_role": scenario.local_role,
            "goal": scenario.goal,
            "language": scenario.language.value,
            "difficulty": scenario.difficulty.value,
            "learner_level": self._learner_level(learner_profile, scenario.language),
            "phrase_pack": phrase_pack or [],
            "attempt_count": 0,
        }

        opening_line = self._call_llm(
            self.get_system_prompt(),
            (
                f"You are a {scenario.local_role} in {scenario.city}, {scenario.country}. "
                f"Greet the customer and set the scene for: {scenario.goal}."
            ),
        )
        return {"mission_context": context, "opening_line": opening_line}

    def generate_response(
        self, learner_input: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the tutor's next in-character response.

        Parameters
        ----------
        learner_input:
            What the learner just said.
        context:
            Current mission context (returned from ``start_mission`` and
            updated each turn).

        Returns
        -------
        dict
            Contains ``response`` (tutor's reply) and updated ``context``.
        """
        context["attempt_count"] = context.get("attempt_count", 0) + 1
        prompt = (
            f"The learner said: \"{learner_input}\"\n"
            f"Scenario goal: {context.get('goal')}\n"
            f"Your role: {context.get('local_role')}\n"
            f"Respond naturally in {context.get('language', 'the target language')}."
        )
        response = self._call_llm(self.get_system_prompt(), prompt)
        return {"response": response, "context": context}

    def should_offer_help(self, learner_input: str, attempt_count: int) -> bool:
        """Decide whether the learner needs explicit help.

        Help is offered when:
        * The learner has attempted more than ``_MAX_UNAIDED_ATTEMPTS`` times, **or**
        * The input is extremely short (≤ 2 chars) suggesting they are stuck.
        """
        if attempt_count > _MAX_UNAIDED_ATTEMPTS:
            return True
        if len(learner_input.strip()) <= 2:
            return True
        return False

    def generate_repair_prompt(self, original_input: str) -> str:
        """Return a prompt that asks the learner to rephrase rather than
        giving them the answer outright.

        Parameters
        ----------
        original_input:
            The learner's problematic utterance.

        Returns
        -------
        str
            A repair prompt in a supportive tone.
        """
        repair = self._call_llm(
            self.get_system_prompt(),
            (
                f"The learner tried to say: \"{original_input}\" but it was unclear. "
                "Gently ask them to try rephrasing without revealing the correct form."
            ),
        )
        return repair

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _learner_level(profile: LearnerProfile, language: "Language") -> str:
        """Extract the estimated level string for *language* from *profile*."""
        from lib.db.models import Language as Lang

        if language == Lang.FRENCH:
            return profile.estimated_french_level.value
        if language == Lang.ITALIAN:
            return profile.estimated_italian_level.value
        return DifficultyLevel.BEGINNER.value
