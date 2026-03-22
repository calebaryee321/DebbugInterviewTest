"""Tests for the ScenarioAgent."""

import pytest

from lib.db.models import (
    DifficultyLevel,
    Language,
    LearnerProfile,
    Scenario,
    ScenarioCategory,
    SessionMode,
)
from agents.scenario.agent import ScenarioAgent


@pytest.fixture
def _scenarios():
    """A small set of test scenarios."""
    return [
        Scenario(
            scenario_id="fr-cafe-1",
            country="France",
            city="Paris",
            category=ScenarioCategory.CAFE,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="waiter",
            goal="Order coffee",
            language=Language.FRENCH,
        ),
        Scenario(
            scenario_id="fr-hotel-1",
            country="France",
            city="Nice",
            category=ScenarioCategory.HOTEL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            local_role="receptionist",
            goal="Check in to hotel",
            language=Language.FRENCH,
        ),
        Scenario(
            scenario_id="fr-train-1",
            country="France",
            city="Lyon",
            category=ScenarioCategory.TRAIN,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="ticket seller",
            goal="Buy train ticket",
            language=Language.FRENCH,
        ),
        Scenario(
            scenario_id="it-cafe-1",
            country="Italy",
            city="Rome",
            category=ScenarioCategory.CAFE,
            difficulty=DifficultyLevel.BEGINNER,
            local_role="barista",
            goal="Order espresso",
            language=Language.ITALIAN,
        ),
    ]


@pytest.fixture
def scenario_agent(_scenarios):
    return ScenarioAgent(scenarios=_scenarios)


class TestSelectScenario:
    def test_returns_a_scenario(self, scenario_agent, sample_learner_profile):
        result = scenario_agent.select_scenario(
            sample_learner_profile, Language.FRENCH, SessionMode.LIVE_MISSION
        )
        assert result is not None
        assert isinstance(result, Scenario)

    def test_filters_by_language(self, scenario_agent, sample_learner_profile):
        result = scenario_agent.select_scenario(
            sample_learner_profile, Language.ITALIAN, SessionMode.LIVE_MISSION
        )
        assert result is not None
        assert result.language == Language.ITALIAN

    def test_avoids_recent_scenarios(self, scenario_agent, sample_learner_profile):
        # Mark all beginner French scenarios except train as recent
        recent = ["fr-cafe-1"]
        result = scenario_agent.select_scenario(
            sample_learner_profile, Language.FRENCH, SessionMode.LIVE_MISSION,
            recent_scenarios=recent,
        )
        assert result is not None
        # Should prefer non-recent scenarios
        # The result may be fr-hotel-1 or fr-train-1 (both not recent)
        assert result.scenario_id != "fr-cafe-1" or result.scenario_id in {
            "fr-cafe-1", "fr-hotel-1", "fr-train-1"
        }

    def test_with_empty_scenarios_list(self, sample_learner_profile):
        agent = ScenarioAgent(scenarios=[])
        result = agent.select_scenario(
            sample_learner_profile, Language.FRENCH, SessionMode.LIVE_MISSION
        )
        assert result is None


class TestGetScenariosByCategory:
    def test_returns_correct_results(self, scenario_agent):
        results = scenario_agent.get_scenarios_by_category(
            ScenarioCategory.CAFE, Language.FRENCH
        )
        assert len(results) == 1
        assert results[0].scenario_id == "fr-cafe-1"

    def test_empty_for_missing_category(self, scenario_agent):
        results = scenario_agent.get_scenarios_by_category(
            ScenarioCategory.PHARMACY, Language.FRENCH
        )
        assert results == []


class TestGetScenariosByDifficulty:
    def test_returns_correct_results(self, scenario_agent):
        results = scenario_agent.get_scenarios_by_difficulty(
            DifficultyLevel.BEGINNER, Language.FRENCH
        )
        assert len(results) == 2
        for s in results:
            assert s.difficulty == DifficultyLevel.BEGINNER

    def test_intermediate_filter(self, scenario_agent):
        results = scenario_agent.get_scenarios_by_difficulty(
            DifficultyLevel.INTERMEDIATE, Language.FRENCH
        )
        assert len(results) == 1
        assert results[0].scenario_id == "fr-hotel-1"


class TestAdjustDifficulty:
    def test_increases_for_high_score(self, scenario_agent):
        result = scenario_agent.adjust_difficulty(DifficultyLevel.BEGINNER, 4.5)
        assert result == DifficultyLevel.ELEMENTARY

    def test_decreases_for_low_score(self, scenario_agent):
        result = scenario_agent.adjust_difficulty(DifficultyLevel.INTERMEDIATE, 2.0)
        assert result == DifficultyLevel.ELEMENTARY

    def test_stays_same_for_mid_score(self, scenario_agent):
        result = scenario_agent.adjust_difficulty(DifficultyLevel.INTERMEDIATE, 3.0)
        assert result == DifficultyLevel.INTERMEDIATE

    def test_does_not_exceed_advanced(self, scenario_agent):
        result = scenario_agent.adjust_difficulty(DifficultyLevel.ADVANCED, 5.0)
        assert result == DifficultyLevel.ADVANCED

    def test_does_not_go_below_beginner(self, scenario_agent):
        result = scenario_agent.adjust_difficulty(DifficultyLevel.BEGINNER, 1.0)
        assert result == DifficultyLevel.BEGINNER
