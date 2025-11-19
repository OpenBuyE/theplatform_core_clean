import os
import requests


class SupabaseREST:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")

        if not self.url or not self.key:
            raise RuntimeError(
                "Falta SUPABASE_URL o SUPABASE_ANON_KEY en los secrets."
            )

        self.base = f"{self.url}/rest/v1"

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def select(self, table: str, filters: str = ""):
        url = f"{self.base}/{table}?{filters}"

        response = requests.get(url, headers=self.headers)

        if not response.ok:
            raise RuntimeError(f"Error Supabase: {response.text}")

        return response.json()

    def insert(self, table: str, json_data: dict):
        url = f"{self.base}/{table}"

        response = requests.post(url, headers=self.headers, json=json_data)

        if not response.ok:
            raise RuntimeError(f"Error insertando: {response.text}")

        return response.json()

    def update(self, table: str, json_data: dict, filters: str):
        url = f"{self.base}/{table}?{filters}"

        response = requests.patch(url, headers=self.headers, json=json_data)

        if not response.ok:
            raise RuntimeError(f"Error actualizando: {response.text}")

        return response.json()
