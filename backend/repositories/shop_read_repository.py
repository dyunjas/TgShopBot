from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import Shop


class ShopReadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, *, shop_id: int) -> Shop | None:
        stmt = (
            select(Shop)
            .where(Shop.id == shop_id)
            .options(
                selectinload(Shop.payment_configs),
                selectinload(Shop.ui_assets),
            )
        )
        return await self.session.scalar(stmt)

