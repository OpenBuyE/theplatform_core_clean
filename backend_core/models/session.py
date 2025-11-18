import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


def generate_hash_seed() -> str:
    """
    Genera una semilla hash determinista para identificar una sesión.
    """
    random_uuid = uuid.uuid4().hex
    return hashlib.sha256(random_uuid.encode()).hexdigest()


def generate_session_id() -> str:
    """
    Genera un ID de sesión legible: S-XXXXX donde XXXXX es un fragmento único.
    """
    unique_part = uuid.uuid4().hex[:10].upper()
    return f"S-{unique_part}"


@dataclass
class Session:
    operator_id: str
    supplier_id: str
    amount: float
    status: str = "parked"  # parked | scheduled | active | closed
    created_at: datetime = field(default_factory=datetime.utcnow)

    scheduled_for: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    chain_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    adjudication_result: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=generate_session_id)
    hash_seed: str = field(default_factory=generate_hash_seed)
