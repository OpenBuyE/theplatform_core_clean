from backend_core.models.session import Session
from backend_core.engine.deterministic_engine import DeterministicAdjudicator


def test_deterministic_engine():
    s1 = Session(operator_id="OP-A", supplier_id="SUP-1", amount=300)
    s2 = Session(operator_id="OP-A", supplier_id="SUP-2", amount=150)

    engine = DeterministicAdjudicator(rule="lowest_amount")

    result = engine.adjudicate([s1, s2])

    assert result["winner_supplier"] == "SUP-2"
    assert len(result["seed"]) == 64

    print("TEST OK: deterministic engine")
