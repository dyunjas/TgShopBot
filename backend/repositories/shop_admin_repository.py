from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Shop


class ShopAdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, shop_id: int) -> Shop | None:
        return await self.session.get(Shop, shop_id)

    async def get_by_token(self, bot_token: str) -> Shop | None:
        stmt = select(Shop).where(Shop.bot_token == bot_token)
        return await self.session.scalar(stmt)

    async def list_all(self) -> list[Shop]:
        stmt = select(Shop).order_by(Shop.id.asc())
        return (await self.session.execute(stmt)).scalars().all()

    async def create(
        self,
        *,
        title: str,
        bot_token: str,
        reviews_channel_id: int,
        is_active: bool,
    ) -> Shop:
        shop = Shop(
            title=title,
            bot_token=bot_token,
            reviews_channel_id=reviews_channel_id,
            is_active=is_active,
        )
        self.session.add(shop)
        await self.session.flush()
        await self.session.refresh(shop)
        return shop

    async def delete(self, shop_id: int) -> None:
        await self.session.execute(delete(Shop).where(Shop.id == shop_id))
