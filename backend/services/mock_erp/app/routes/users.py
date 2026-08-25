from fastapi import APIRouter, HTTPException

from ..database import get_one

router = APIRouter(prefix="/erp/users", tags=["users"])


@router.get("/{user_id}/permissions")
def get_user_permissions(user_id: str):
    user = get_one("users", user_id)
    permissions = get_one("permissions", user_id)
    if not user or not permissions:
        raise HTTPException(404, detail={"error": "USER_NOT_FOUND", "user_id": user_id})
    return {"user": user, "permissions": permissions}
