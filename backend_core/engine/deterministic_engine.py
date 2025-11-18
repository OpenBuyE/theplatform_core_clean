import hashlib
import json
from typing import List, Dict, Any
from backend_core.models.session import Session


class DeterministicAdjudicator:
    """
    Motor determinista de adjudicación.
    Produce siempre el mismo resultado dado un mismo conjunto de sesiones.
    """

    def __init__(self, rule: str = "lowest_amount"):
        self.rule = rule

    def make_seed(self, sessions: List[Session]) -> str:
        """
        Construye una semilla determinista basada en:
        - IDs de sesión
        - hash_seed interno
        - montos
        - operador
        """
        data = [
            {
                "id": s.id,
                "operator": s.operator_id,
                "supplier": s.supplier_id,
                "amount": s.amount,
                "hash": s.hash_seed,
            }
            for s in sessions
        ]
        raw = json.dumps(data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def adjudicate(self, sessions: List[Session]) -> Dict[str, Any]:
        """
        Devuelve:
        - ganador
        - seed usada
        - listado ordenado segun reglas
        """

        if not sessions:
            return {"winner": None, "reason": "No sessions provided"}

        seed = self.make_seed(sessions)

        if self.rule == "lowest_amount":
            ordered = sorted(sessions, key=lambda s: s.amount)
        else:
            ordered = sessions  # extender reglas más adelante

        winner = ordered[0]

        return {
            "winner_id": winner.id,
            "winner_supplier": winner.supplier_id,
            "seed": seed,
            "ordered": [s.id for s in ordered],
        }
