from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import require_role, CurrentAdmin
from backend.database.models import ShopTransaction

router = APIRouter(tags=["transactions"])


@router.get("")
async def list_transactions(
    shop_id: int | None = Query(default=None),
    paid: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    stmt = (
        select(ShopTransaction)
        .options(selectinload(ShopTransaction.user))
        .order_by(desc(ShopTransaction.created_at))
    )

    if shop_id is not None:
        stmt = stmt.where(ShopTransaction.shop_id == shop_id)
    if paid is not None:
        stmt = stmt.where(ShopTransaction.paid.is_(paid))

    stmt = stmt.limit(limit).offset(offset)

    rows = (await session.execute(stmt)).scalars().all()

    return [
        {
            "id": t.id,
            "shop_id": t.shop_id,
            "transaction_id": t.transaction_id,
            "order_id": t.order_id,
            "amount": t.amount,
            "payment_system": t.payment_system,
            "paid": t.paid,
            "paid_at": t.paid_at,
            "created_at": t.created_at,
            "user_id": t.user_id,
            "user_tg_id": t.user.tg_id if t.user else None,
            "username": t.user.username if t.user else None,
        }
        for t in rows
    ]
