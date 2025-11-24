# tests/factories/session_factory.py

def fake_session(
    id="sess-001",
    product_id="prod-001",
    organization_id="org-001",
    series_id="series-001",
    sequence_number=1,
    status="active",
    capacity=3,
    pax_registered=3
):
    return {
        "id": id,
        "product_id": product_id,
        "organization_id": organization_id,
        "series_id": series_id,
        "sequence_number": sequence_number,
        "status": status,
        "capacity": capacity,
        "pax_registered": pax_registered,
        "activated_at": None,
        "expires_at": None,
    }
