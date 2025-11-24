# backend_core/services/supabase_client.py

import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL o SUPABASE_KEY no configurados.")

# ========================================================
# Cliente mínimo compatible con .table().select().eq().execute()
# ========================================================

class QueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filters = []
        self.order_field = None
        self._single = False
        self.columns = "*"

    # ----------------------
    def select(self, columns="*"):
        self.columns = columns
        return self

    # ----------------------
    def eq(self, field, value):
        self.filters.append(f"{field}=eq.{value}")
        return this

    # ----------------------
    def order(self, field, desc=False):
        self.order_field = (field, desc)
        return self

    # ----------------------
    def single(self):
        self._single = True
        return self

    # ----------------------
    def _build_url(self):
        url = f"{SUPABASE_URL}/rest/v1/{self.table_name}?select={self.columns}"
        if self.filters:
            for f in self.filters:
                url += f"&{f}"
        if self.order_field:
            field, desc = self.order_field
            url += f"&order={field}.{'desc' if desc else 'asc'}"
        if self._single:
            url += "&limit=1"
        return url

    # ----------------------
    def execute(self, method="GET", json=None):
        url = self._build_url()

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=json)
        elif method == "PATCH":
            r = requests.patch(url, headers=headers, json=json)
        else:
            raise ValueError("Método HTTP no soportado")

        if r.status_code >= 400:
            raise Exception(f"Supabase error {r.status_code}: {r.text}")

        try:
            return type("Response", (), {"data": r.json()})
        except Exception:
            return type("Response", (), {"data": None})


# ========================================================
# API pública: supabase.table("nombre")
# ========================================================

def table(name: str) -> QueryBuilder:
    return QueryBuilder(name)


# alias para compatibilidad:
supabase = type("SupabaseWrapper", (), {"table": table})
