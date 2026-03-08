from __future__ import annotations

from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import ShopCategory, ShopItem


class DeleteCategoryResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    HAS_ITEMS = "has_items"
    HAS_SUBCATEGORIES = "has_subcategories"


UNSET = object()


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, *, shop_id: int, parent_id: int | None = None) -> list[ShopCategory]:
        stmt = (
            select(ShopCategory)
            .options(selectinload(ShopCategory.parent))
            .where(
                ShopCategory.shop_id == shop_id,
                ShopCategory.parent_id == parent_id,
            )
            .order_by(ShopCategory.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, *, shop_id: int, category_id: int) -> ShopCategory | None:
        stmt = select(ShopCategory).where(
            ShopCategory.shop_id == shop_id,
            ShopCategory.id == category_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        shop_id: int,
        title: str,
        img: str,
        parent_id: int | None = None,
    ) -> ShopCategory:
        category = ShopCategory(
            shop_id=shop_id,
            title=title,
            img=img,
            parent_id=parent_id,
        )
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def update(
        self,
        *,
        shop_id: int,
        category_id: int,
        title: str | object = UNSET,
        img: str | object = UNSET,
        parent_id: int | None | object = UNSET,
    ) -> ShopCategory | None:
        category = await self.get_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            return None

        if title is not UNSET:
            category.title = str(title)

        if img is not UNSET:
            category.img = str(img)

        if parent_id is not UNSET:
            category.parent_id = parent_id

        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, category: ShopCategory) -> None:
        await self.session.delete(category)
        await self.session.flush()

    async def has_items(self, *, shop_id: int, category_id: int) -> bool:
        item_id = await self.session.scalar(
            select(ShopItem.id)
            .where(ShopItem.shop_id == shop_id, ShopItem.category_id == category_id)
            .limit(1)
        )
        return bool(item_id)

    async def has_children(self, *, shop_id: int, category_id: int) -> bool:
        child_id = await self.session.scalar(
            select(ShopCategory.id)
            .where(ShopCategory.shop_id == shop_id, ShopCategory.parent_id == category_id)
            .limit(1)
        )
        return bool(child_id)

