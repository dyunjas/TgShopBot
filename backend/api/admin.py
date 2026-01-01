from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import ShopOrder

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
        "created_at": a.created_at,
    }


@router.get("/balance")
async def balance(current: CurrentAdmin = Depends(require_role("operator", "superadmin"))):
    return {"tg_id": current.tg_id, "balance": current.admin.balance}


@router.get("/my-orders")
async def my_orders(
    status: str = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("operator", "superadmin")),
):
    stmt = select(ShopOrder).options(
        selectinload(ShopOrder.user),
        selectinload(ShopOrder.shop),
    )

    if current.role == "operator":
        stmt = stmt.where(ShopOrder.executor_admin_id == current.id)

    if status and status != "all":
        stmt = stmt.where(ShopOrder.status == status)

    stmt = (
        stmt.order_by(ShopOrder.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    rows = (await session.execute(stmt)).scalars().all()

    return [
        {
            "order_id": o.order_id,
            "shop_id": o.shop_id,
            "shop_title": o.shop.title if o.shop else None,
            "title": o.title,
            "price": o.price,
            "status": o.status,
            "created_at": o.created_at,
            "user_tg_id": o.user.tg_id if o.user else None,
            "drop_topic_id": o.drop_topic_id,
            "executor_admin_id": o.executor_admin_id,
            "executor_name": getattr(o, "executor_name", None),
        }
        for o in rows
    ]
