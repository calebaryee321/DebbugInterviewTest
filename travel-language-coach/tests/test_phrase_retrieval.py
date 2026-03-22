"""Tests for the PhraseRetrievalAgent."""

import pytest

from lib.db.models import (
    DifficultyLevel,
    Language,
    Scenario,
    ScenarioCategory,
)
from agents.phrase_retrieval.agent import PhraseRetrievalAgent


@pytest.fixture
def phrase_agent():
    agent = PhraseRetrievalAgent()
    agent.add_phrase_pack("french", "cafe", {
        "phrases": [
            "Bonjour, un café s'il vous plaît",
            "L'addition, s'il vous plaît",
        ],
        "polite_alternatives": {
            "Je veux": "Je voudrais",
            "Donne-moi": "Pourriez-vous me donner",
        },
        "culture_notes": [
            "Always greet with Bonjour before ordering",
        ],
    })
    return agent


class TestAddAndLoadPhrasePack:
    def test_add_and_load(self, phrase_agent):
        pack = phrase_agent.load_phrase_pack("french", "cafe")
        assert len(pack["phrases"]) == 2
        assert "Je veux" in pack["polite_alternatives"]
        assert len(pack["culture_notes"]) == 1

    def test_load_nonexistent_returns_empty(self, phrase_agent):
        pack = phrase_agent.load_phrase_pack("german", "hotel")
        assert pack["phrases"] == []
        assert pack["polite_alternatives"] == {}
        assert pack["culture_notes"] == []


class TestGetPhrasesForScenario:
    def test_returns_phrases(self, phrase_agent):
        scenario = Scenario(
            country="France",
            city="Paris",
            category=ScenarioCategory.CAFE,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="waiter",
            goal="Order coffee",
            language=Language.FRENCH,
        )
        phrases = phrase_agent.get_phrases_for_scenario(scenario)
        assert len(phrases) == 2

    def test_returns_empty_for_unknown_scenario(self, phrase_agent):
        scenario = Scenario(
            country="Italy",
            city="Rome",
            category=ScenarioCategory.HOTEL,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="receptionist",
            goal="Check in",
            language=Language.ITALIAN,
        )
        phrases = phrase_agent.get_phrases_for_scenario(scenario)
        assert phrases == []


class TestGetPoliteAlternatives:
    def test_returns_stored_alternative(self, phrase_agent):
        alts = phrase_agent.get_polite_alternatives("Je veux", "french")
        assert "Je voudrais" in alts

    def test_fallback_for_unknown_phrase(self, phrase_agent):
        alts = phrase_agent.get_polite_alternatives("random phrase", "french")
        # Falls back to LLM placeholder
        assert len(alts) == 1
        assert "[LLM placeholder]" in alts[0]


class TestGetSimplifiedVersion:
    def test_returns_string(self, phrase_agent):
        result = phrase_agent.get_simplified_version(
            "Pourriez-vous me donner l'addition", "french"
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetCultureNotes:
    def test_returns_stored_notes(self, phrase_agent):
        notes = phrase_agent.get_culture_notes("France", "cafe")
        assert len(notes) >= 1
        assert any("Bonjour" in n for n in notes)

    def test_fallback_for_unknown(self, phrase_agent):
        notes = phrase_agent.get_culture_notes("Germany", "restaurant")
        assert len(notes) == 1
        assert "[LLM placeholder]" in notes[0]
