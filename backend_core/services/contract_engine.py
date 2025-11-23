from backend_core.services.payment_session_repository import (
    create_payment_session,
)
from backend_core.services.audit_repository import AuditRepository

audit_repo = AuditRepository()


def on_session_awarded(session_id: str, adjudicatario_user_id: str) -> None:

    # Cargar la sesión para saber el organization_id y expected_amount
    session = supabase_client.table("ca_sessions").select("*").eq("id", session_id).single().execute().data

    expected_amount = float(session["capacity"]) * float(session["price"])  # depende de tu modelo real
    organization_id = session["organization_id"]

    # Crear payment_session si no existe
    create_payment_session(
        session_id=session_id,
        organization_id=organization_id,
        expected_amount=expected_amount,
    )

    audit_repo.log(
        action="PAYMENT_SESSION_CREATED",
        session_id=session_id,
        user_id=adjudicatario_user_id,
        metadata={"expected_amount": expected_amount},
    )
