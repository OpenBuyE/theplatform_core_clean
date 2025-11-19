from dataclasses import dataclass
from typing import List
from backend_core.services.supabase_client import SupabaseREST


@dataclass
class SessionRecord:
    id: str
    product_id: str
    operator_code: str
    amount: float
    status: str


class SessionRepository:
    TABLE = "sessions"

    def __init__(self):
        self.client = SupabaseREST()

    def get_by_status(self, status: str) -> List[SessionRecord]:
        rows = self.client.select(
            self.TABLE,
            filters=f"status=eq.{status}"
        )

        return [
            SessionRecord(
                id=row["id"],
                product_id=row["product_id"],
                operator_code=row["operator_code"],
                amount=float(row["amount"]),
                status=row["status"]
            )
            for row in rows
        ]

    def get_parked(self):
        return self.get_by_status("parked")

    def get_active(self):
        return self.get_by_status("active")

