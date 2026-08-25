from datetime import UTC, datetime

from fastapi import APIRouter

from ..database import count, find_many, insert
from ..schemas import TicketCreate

router = APIRouter(prefix="/erp/tickets", tags=["tickets"])


@router.post("", status_code=201)
def create_ticket(request: TicketCreate):
    existing = find_many("tickets", {"run_id": request.run_id})
    if existing:
        return {**existing[0], "idempotent_replay": True}
    ticket_id = f"TKT-{datetime.now(UTC).year}-{count('tickets') + 1:04d}"
    payload = {
        "ticket_id": ticket_id,
        **request.model_dump(),
        "status": "OPEN",
        "created_at": datetime.now(UTC).isoformat(),
        "idempotent_replay": False,
    }
    return insert("tickets", ticket_id, payload)
