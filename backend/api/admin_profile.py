from fastapi import APIRouter, Depends
from .utils.admin_role import CurrentAdmin, require_role

router = APIRouter(tags=["admin"])

@router.get("/me")
async def me(current: CurrentAdmin = Depends(require_role("operator", "superadmin"))):
    a = current.admin
    return {
        "id": a.id,
        "tg_id": a.tg_id,
        "username": a.username,
        "role": getattr(a, "role", "operator"),
        "balance": a.balance,
    }

@router.get("/balance")
async def balance(current: CurrentAdmin = Depends(require_role("operator", "superadmin"))):
    return {"balance": current.admin.balance}
