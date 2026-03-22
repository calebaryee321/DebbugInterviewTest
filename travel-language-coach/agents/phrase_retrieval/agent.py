"""Phrase Retrieval Agent – manages phrase packs, polite alternatives, and culture notes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from lib.db.models import Language, Scenario, ScenarioCategory


# Type alias for the nested phrase store.
_PhraseStore = Dict[str, Dict[str, Dict[str, Any]]]
# e.g. {"french": {"restaurant": {"phrases": [...], "polite_alternatives": {...}, "culture_notes": [...]}}}


class PhraseRetrievalAgent(BaseAgent):
    """Manages an in-memory phrase store organised by language and category.

    The store structure is::

        {
            "french": {
                "restaurant": {
                    "phrases": ["Bonjour, une table pour deux s'il vous plaît", ...],
                    "polite_alternatives": {
                        "Je veux": "Je voudrais",
                        ...
                    },
                    "culture_notes": ["Always greet with 'Bonjour' before ordering", ...]
                }
            }
        }
    """

    def __init__(self) -> None:
        self._store: _PhraseStore = {}

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def agent_name(self) -> str:
        return "phrase_retrieval"

    @property
    def agent_role(self) -> str:
        return (
            "Retrieve and manage phrase packs, polite alternatives, simplified "
            "versions, and culture notes for each supported language and "
            "scenario category."
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate method based on *action*.

        Supported actions: ``load``, ``for_scenario``, ``polite``,
        ``simplified``, ``add``, ``culture_notes``.
        """
        action = payload.get("action")
        if action == "load":
            return {
                "phrase_pack": self.load_phrase_pack(
                    payload["language"], payload["category"]
                )
            }
        if action == "for_scenario":
            scenario = (
                Scenario(**payload["scenario"])
                if isinstance(payload["scenario"], dict)
                else payload["scenario"]
            )
            return {"phrases": self.get_phrases_for_scenario(scenario)}
        if action == "polite":
            return {
                "alternatives": self.get_polite_alternatives(
                    payload["phrase"], payload["language"]
                )
            }
        if action == "simplified":
            return {
                "simplified": self.get_simplified_version(
                    payload["phrase"], payload["language"]
                )
            }
        if action == "add":
            self.add_phrase_pack(
                payload["language"], payload["category"], payload["phrases"]
            )
            return {"added": True}
        if action == "culture_notes":
            return {
                "notes": self.get_culture_notes(
                    payload["country"], payload["category"]
                )
            }
        return {"error": f"Unknown action: {action}"}

    def get_system_prompt(self) -> str:
        return (
            "You are the Phrase Retrieval Agent for a Travel Language Coach. "
            "You maintain a library of useful phrases organised by language and "
            "real-world scenario category (restaurant, hotel, train, etc.). "
            "When asked:\n"
            "1. Return the most relevant phrases for the current scenario and "
            "learner level.\n"
            "2. Provide polite alternatives when the learner's phrasing is too "
            "blunt or informal.\n"
            "3. Offer simplified versions when the learner struggles with a "
            "complex phrase.\n"
            "4. Include culture notes (greetings etiquette, tipping customs, etc.) "
            "relevant to the country and scenario."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_phrase_pack(
        self, language: str, category: str
    ) -> Dict[str, Any]:
        """Load and return the phrase pack for *language* / *category*.

        Returns an empty structure if nothing has been added yet.
        """
        lang_store = self._store.get(language, {})
        return lang_store.get(
            category,
            {"phrases": [], "polite_alternatives": {}, "culture_notes": []},
        )

    def get_phrases_for_scenario(self, scenario: Scenario) -> List[str]:
        """Return the phrase list relevant to *scenario*.

        Looks up phrases by ``scenario.language`` and
        ``scenario.category``.
        """
        pack = self.load_phrase_pack(
            scenario.language.value, scenario.category.value
        )
        return pack.get("phrases", [])

    def get_polite_alternatives(
        self, phrase: str, language: str
    ) -> List[str]:
        """Return polite versions of *phrase* in *language*.

        Searches all categories for the language.  If the phrase is found
        as a key in ``polite_alternatives``, returns a list containing
        the mapped value.  Otherwise delegates to the LLM placeholder.
        """
        lang_store = self._store.get(language, {})
        results: List[str] = []
        for _cat, pack in lang_store.items():
            alts = pack.get("polite_alternatives", {})
            if phrase in alts:
                results.append(alts[phrase])
        if results:
            return results
        # Fallback: ask LLM
        llm_result = self._call_llm(
            self.get_system_prompt(),
            f"Provide polite alternatives for the {language} phrase: '{phrase}'",
        )
        return [llm_result]

    def get_simplified_version(self, phrase: str, language: str) -> str:
        """Return a simpler version of *phrase* in *language*.

        Delegates to the LLM placeholder since simplification is
        context-dependent.
        """
        return self._call_llm(
            self.get_system_prompt(),
            f"Simplify this {language} phrase for a beginner: '{phrase}'",
        )

    def add_phrase_pack(
        self,
        language: str,
        category: str,
        phrases: Dict[str, Any],
    ) -> None:
        """Add or merge a phrase pack into the store.

        Parameters
        ----------
        language:
            Target language key (e.g. ``"french"``).
        category:
            Scenario category key (e.g. ``"restaurant"``).
        phrases:
            A dict with optional keys ``"phrases"`` (list[str]),
            ``"polite_alternatives"`` (dict[str,str]),
            ``"culture_notes"`` (list[str]).
        """
        lang_store = self._store.setdefault(language, {})
        existing = lang_store.get(
            category,
            {"phrases": [], "polite_alternatives": {}, "culture_notes": []},
        )
        existing["phrases"] = list(
            {*existing["phrases"], *phrases.get("phrases", [])}
        )
        existing["polite_alternatives"].update(
            phrases.get("polite_alternatives", {})
        )
        existing["culture_notes"] = list(
            {*existing["culture_notes"], *phrases.get("culture_notes", [])}
        )
        lang_store[category] = existing

    def get_culture_notes(self, country: str, category: str) -> List[str]:
        """Return culture tips for *country* / *category*.

        Scans all languages since culture notes are country-specific.
        Falls back to an LLM placeholder if nothing is stored.
        """
        notes: List[str] = []
        for _lang, cats in self._store.items():
            pack = cats.get(category, {})
            notes.extend(pack.get("culture_notes", []))
        if notes:
            return notes
        llm_result = self._call_llm(
            self.get_system_prompt(),
            f"Provide culture tips for {category} situations in {country}.",
        )
        return [llm_result]
