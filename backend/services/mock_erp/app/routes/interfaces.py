from fastapi import APIRouter

from ..database import find_many

router = APIRouter(prefix="/erp/interfaces", tags=["interfaces"])


@router.get("/logs")
def get_interface_logs(
    claim_id: str | None = None,
    interface: str | None = None,
    correlation_id: str | None = None,
):
    filters = {
        key: value
        for key, value in {
            "claim_id": claim_id,
            "interface": interface,
            "correlation_id": correlation_id,
        }.items()
        if value is not None
    }
    return {"items": find_many("interface_logs", filters), "filters": filters}
