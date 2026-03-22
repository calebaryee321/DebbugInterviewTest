"""Utility helpers for loading scenario, phrase-pack, and culture-note data.

All JSON data files live under ``travel-language-coach/data/``.  The loader
functions resolve paths relative to that directory so callers never need to
hard-code filesystem locations.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .models import Scenario

logger = logging.getLogger(__name__)

# Root of the ``data/`` tree — two levels up from this file, then into ``data/``.
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_COUNTRY_FOLDER: Dict[str, str] = {
    "france": "france",
    "italy": "italy",
}


def _read_json(path: Path) -> Any:
    """Read and parse a JSON file, raising a clear error if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _country_key(country: str) -> str:
    """Normalise a country name to its folder key."""
    key = country.strip().lower()
    if key not in _COUNTRY_FOLDER:
        raise ValueError(
            f"Unsupported country '{country}'. "
            f"Available: {', '.join(sorted(_COUNTRY_FOLDER))}"
        )
    return _COUNTRY_FOLDER[key]


# ------------------------------------------------------------------
# Scenarios
# ------------------------------------------------------------------


def load_scenarios(country: str) -> List[Scenario]:
    """Load all scenarios for *country* and return validated model objects.

    Parameters
    ----------
    country:
        Country name (case-insensitive), e.g. ``"France"`` or ``"italy"``.

    Returns
    -------
    list[Scenario]
        A list of :class:`Scenario` instances parsed from the JSON file.
    """
    key = _country_key(country)
    path = _DATA_DIR / "scenarios" / key / "scenarios.json"
    raw: list = _read_json(path)
    scenarios = [Scenario(**item) for item in raw]
    logger.info("Loaded %d scenarios for %s", len(scenarios), country)
    return scenarios


def load_all_scenarios() -> List[Scenario]:
    """Load scenarios for every supported country."""
    all_scenarios: List[Scenario] = []
    for country in _COUNTRY_FOLDER:
        try:
            all_scenarios.extend(load_scenarios(country))
        except FileNotFoundError:
            logger.warning("No scenario file found for %s — skipping.", country)
    logger.info("Loaded %d total scenarios", len(all_scenarios))
    return all_scenarios


# ------------------------------------------------------------------
# Phrase packs
# ------------------------------------------------------------------


def load_phrase_pack(country: str) -> Dict[str, Any]:
    """Load the phrase-pack dictionary for *country*.

    The returned dict is keyed by scenario category (``"restaurant"``,
    ``"cafe"``, etc.) with values containing ``phrases``,
    ``polite_alternatives``, and ``culture_notes``.
    """
    key = _country_key(country)
    path = _DATA_DIR / "phrasepacks" / key / "phrases.json"
    data: dict = _read_json(path)
    logger.info("Loaded phrase pack for %s (%d categories)", country, len(data))
    return data


# ------------------------------------------------------------------
# Culture notes
# ------------------------------------------------------------------


def load_culture_notes(country: str) -> Dict[str, Any]:
    """Load culture-note data for *country*.

    Returns the full parsed JSON object, which includes top-level metadata
    (``country``, ``language``) and a ``categories`` mapping.
    """
    key = _country_key(country)
    path = _DATA_DIR / "culture" / f"{key}.json"
    data: dict = _read_json(path)
    logger.info("Loaded culture notes for %s", country)
    return data
