from fastapi import APIRouter, HTTPException

from ..database import get_one

router = APIRouter(prefix="/erp/claims", tags=["vouchers"])


@router.get("/{claim_id}/voucher-status")
def get_voucher_status(claim_id: str):
    voucher = get_one("vouchers", claim_id)
    if not voucher:
        raise HTTPException(404, detail={"error": "VOUCHER_NOT_FOUND", "claim_id": claim_id})
    return voucher
