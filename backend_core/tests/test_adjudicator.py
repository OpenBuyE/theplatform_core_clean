"""
test_adjudicator.py
Pruebas funcionales del motor determinista de adjudicación.

NOTA IMPORTANTE:
Estas pruebas NO mockean Supabase: trabajan contra la base real.
Por eso debes usar una base de datos de desarrollo (staging).

Pruebas incluidas:
1. Crear sesión de prueba y participantes
2. Probar adjudicación sin seed pública
3. Probar adjudicación con seed pública
4. Comprobar reproducibilidad (misma seed → mismo ganador)
5. Comprobar expiración (no adjudica)
6. Comprobar rolling: se activa siguiente sesión automáticamente

Para ejecutar:
    python backend_core/tests/test_adjudicator.py
"""

import uuid
from datetime import datetime, timedelta
from time import sleep

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.adjudicator_repository import adjudicator_repository
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.session_engine import session_engine


# ---------------------------------------------------------
# Helper para crear sesión de prueba
# ---------------------------------------------------------
def create_test_session(sequence_number, expires_after_seconds=3600):
    session_id = str(uuid.uuid4())
    product_id = "TEST-PROD"
    series_id = "TEST-SERIES"
    organization_id = "TEST-ORG"

    now = datetime.utcnow()
    expires_at = (now + timedelta(seconds=expires_after_seconds)).isoformat()

    # Insertar sesión directamente en Supabase
    supabase = session_repository.supabase  # recuperación indirecta
    response = supabase.table("sessions").insert({
        "id": session_id,
        "product_id": product_id,
        "series_id": series_id,
        "sequence_number": sequence_number,
        "organization_id": organization_id,
        "capacity": 3,
        "pax_registered": 0,
        "status": "active",
        "activated_at": now.isoformat(),
        "expires_at": expires_at
    }).execute()

    assert response.data, "No se pudo crear la sesión de prueba"

    print(f"✓ Sesión creada: {session_id}")
    return session_id


# ---------------------------------------------------------
# Helper para inscribir participantes
# ---------------------------------------------------------
def add_test_participants(session_id, count=3):
    for i in range(count):
        participant_repository.add_participant(
            session_id=session_id,
            user_id=f"user-{i}",
            organization_id="TEST-ORG",
            amount=10.0,
            price=10.0,
            quantity=1
        )
    print(f"✓ {count} participantes añadidos a la sesión {session_id}")


# ---------------------------------------------------------
# Test 1: Adjudicación sin seed pública
# ---------------------------------------------------------
def test_adjudication_without_seed():
    print("\n=== TEST 1: Adjudicación sin seed pública ===")
    session_id = create_test_session(sequence_number=1)

    add_test_participants(session_id, count=3)

    winner = adjudicator_engine.adjudicate_session(session_id)
    assert winner is not None, "No se generó ganador"

    print(f"GANADOR: {winner['user_id']}")
    return winner


# ---------------------------------------------------------
# Test 2: Adjudicación con seed pública
# ---------------------------------------------------------
def test_adjudication_with_seed():
    print("\n=== TEST 2: Adjudicación con seed pública ===")
    session_id = create_test_session(sequence_number=2)

    add_test_participants(session_id, count=3)

    # Fijamos una seed pública que haga el resultado reproducible
    seed = "PUBLIC-SEED-12345"
    adjudicator_repository.set_public_seed_for_session(session_id, seed)

    winner = adjudicator_engine.adjudicate_session(session_id)
    assert winner is not None

    print(f"GANADOR con seed: {winner['user_id']}")
    return session_id, winner


# ---------------------------------------------------------
# Test 3: Reproducibilidad determinista
# ---------------------------------------------------------
def test_reproducibility():
    print("\n=== TEST 3: Reproducibilidad determinista ===")
    session_id, first_winner = test_adjudication_with_seed()

    # Adjudicación repetida debería producir mismo winner
    winner2 = adjudicator_engine.adjudicate_session(session_id)
    assert winner2["user_id"] == first_winner["user_id"], "No es determinista"

    print(f"GANADOR 1: {first_winner['user_id']}")
    print(f"GANADOR 2: {winner2['user_id']}")
    print("✓ Reproducible")


# ---------------------------------------------------------
# Test 4: Expiración sin completar aforo
# ---------------------------------------------------------
def test_expiration_without_award():
    print("\n=== TEST 4: Expiración sin completar aforo ===")
    session_id = create_test_session(sequence_number=3, expires_after_seconds=2)

    # NO añadimos participantes → no completa aforo

    print("Esperando expiración…")
    sleep(3)

    session_engine.process_expired_sessions()

    session = session_repository.get_session_by_id(session_id)
    assert session["status"] == "finished"
    assert session["pax_registered"] < session["capacity"]

    print("✓ Sesión expirada correctamente sin adjudicar")


# ---------------------------------------------------------
# Test 5: Rolling (activar siguiente sesión)
# ---------------------------------------------------------
def test_rolling():
    print("\n=== TEST 5: Rolling automático de sesiones ===")

    # Crear 2 sesiones consecutivas en la serie
    s1 = create_test_session(sequence_number=10)
    s2 = create_test_session(sequence_number=11)

    # Poner s2 en estado parked
    supabase = session_repository.supabase
    supabase.table("sessions").update({
        "status": "parked",
        "activated_at": None,
        "finished_at": None
    }).eq("id", s2).execute()

    # Completar aforo de la primera sesión y adjudicar
    add_test_participants(s1, count=3)
    adjudicator_engine.adjudicate_session(s1)

    # Comprobar que s2 ha sido activada
    session2 = session_repository.get_session_by_id(s2)
    assert session2["status"] == "active", "La siguiente sesión no fue activada"

    print("✓ Rolling correcto: s2 activada automáticamente")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n🔥 INICIANDO TESTS DEL MOTOR DETERMINISTA 🔥")

    test_adjudication_without_seed()
    test_adjudication_with_seed()
    test_reproducibility()
    test_expiration_without_award()
    test_rolling()

    print("\n🎉 TODOS LOS TESTS HAN FINALIZADO 🎉")
