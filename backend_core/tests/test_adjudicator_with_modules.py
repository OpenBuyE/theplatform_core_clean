# tests/test_adjudicator_with_modules.py

import pytest
from backend_core.services.adjudicator_engine import adjudicator_engine


def test_adjudicator_rejects_non_deterministic():
    with pytest.raises(Exception):
        adjudicator_engine.adjudicate("sess-non-deterministic")
