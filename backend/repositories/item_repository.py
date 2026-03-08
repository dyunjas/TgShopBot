from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import ShopCategory, ShopItem
from .category_repository import UNSET


class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, *, shop_id: int, category_id: int | None = None) -> list[ShopItem]:
        stmt = (
            select(ShopItem)
            .options(selectinload(ShopItem.category).selectinload(ShopCategory.parent))
            .where(ShopItem.shop_id == shop_id)
            .order_by(ShopItem.id.asc())
        )
        if category_id is not None:
            stmt = stmt.where(ShopItem.category_id == category_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, *, shop_id: int, item_id: int) -> ShopItem | None:
        stmt = select(ShopItem).where(
            ShopItem.shop_id == shop_id,
            ShopItem.id == item_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        shop_id: int,
        title: str,
        price: int,
        description: str | None,
        img: str,
        category_id: int,
    ) -> ShopItem:
        item = ShopItem(
            shop_id=shop_id,
            title=title,
            price=price,
            description=description,
            img=img,
            category_id=category_id,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update(
        self,
        *,
        shop_id: int,
        item_id: int,
        title: str | object = UNSET,
        price: int | object = UNSET,
        description: str | None | object = UNSET,
        img: str | object = UNSET,
        category_id: int | object = UNSET,
    ) -> ShopItem | None:
        item = await self.get_by_id(shop_id=shop_id, item_id=item_id)
        if not item:
            return None

        if title is not UNSET:
            item.title = str(title)

        if price is not UNSET:
            item.price = int(price)

        if description is not UNSET:
            item.description = description

        if img is not UNSET:
            item.img = str(img)

        if category_id is not UNSET:
            item.category_id = int(category_id)

        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: ShopItem) -> None:
        await self.session.delete(item)
        await self.session.flush()

