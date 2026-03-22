"""Tests for the data loader utility functions."""

import pytest

from lib.db.data_loader import (
    load_all_scenarios,
    load_culture_notes,
    load_phrase_pack,
    load_scenarios,
)
from lib.db.models import Scenario


class TestLoadScenarios:
    def test_load_france(self):
        scenarios = load_scenarios("france")
        assert len(scenarios) == 12
        assert all(isinstance(s, Scenario) for s in scenarios)

    def test_load_italy(self):
        scenarios = load_scenarios("italy")
        assert len(scenarios) == 12
        assert all(isinstance(s, Scenario) for s in scenarios)

    def test_case_insensitive(self):
        scenarios = load_scenarios("France")
        assert len(scenarios) == 12

    def test_nonexistent_country_raises(self):
        with pytest.raises(ValueError, match="Unsupported country"):
            load_scenarios("germany")


class TestLoadAllScenarios:
    def test_returns_24_scenarios(self):
        scenarios = load_all_scenarios()
        assert len(scenarios) == 24

    def test_all_have_required_fields(self):
        scenarios = load_all_scenarios()
        for s in scenarios:
            assert s.country
            assert s.city
            assert s.category
            assert s.difficulty
            assert s.local_role
            assert s.goal
            assert s.language


class TestLoadPhrasePack:
    def test_load_france(self):
        pack = load_phrase_pack("france")
        assert isinstance(pack, dict)
        assert len(pack) > 0

    def test_load_italy(self):
        pack = load_phrase_pack("italy")
        assert isinstance(pack, dict)
        assert len(pack) > 0

    def test_nonexistent_country_raises(self):
        with pytest.raises(ValueError, match="Unsupported country"):
            load_phrase_pack("germany")


class TestLoadCultureNotes:
    def test_load_france(self):
        notes = load_culture_notes("france")
        assert isinstance(notes, dict)
        assert "country" in notes or len(notes) > 0

    def test_load_italy(self):
        notes = load_culture_notes("italy")
        assert isinstance(notes, dict)

    def test_nonexistent_country_raises(self):
        with pytest.raises(ValueError, match="Unsupported country"):
            load_culture_notes("germany")
