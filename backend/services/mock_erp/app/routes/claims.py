from fastapi import APIRouter, HTTPException

from ..database import get_one

router = APIRouter(prefix="/erp/claims", tags=["claims"])


@router.get("/{claim_id}/status")
def get_claim_status(claim_id: str):
    claim = get_one("claims", claim_id)
    if not claim:
        raise HTTPException(404, detail={"error": "CLAIM_NOT_FOUND", "claim_id": claim_id})
    return claim
