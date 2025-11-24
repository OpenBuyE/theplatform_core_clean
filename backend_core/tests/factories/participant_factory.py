# tests/factories/participant_factory.py

def fake_participant(id):
    return {
        "id": id,
        "user_id": f"usr-{id}",
        "amount": 10,
        "price": 30,
        "quantity": 1,
        "is_awarded": False,
    }
