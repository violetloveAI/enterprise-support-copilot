from fastapi import APIRouter, HTTPException

from ..database import get_one

router = APIRouter(prefix="/erp/claims", tags=["approvals"])


@router.get("/{claim_id}/approval-flow")
def get_approval_flow(claim_id: str):
    flow = get_one("approval_flows", claim_id)
    if not flow:
        raise HTTPException(404, detail={"error": "FLOW_NOT_FOUND", "claim_id": claim_id})
    return flow
