from __future__ import annotations

from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import ShopCategory, ShopItem, Shop


class DeleteCategoryResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    HAS_ITEMS = "has_items"
    HAS_SUBCATEGORIES = "has_subcategories"


class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_categories(self, *, shop_id: int, parent_id: int | None = None) -> list[ShopCategory]:
        stmt = (
            select(ShopCategory)
            .options(selectinload(ShopCategory.parent))
            .where(
                ShopCategory.shop_id == shop_id,
                ShopCategory.parent_id == parent_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_categories(self, *, shop_id: int) -> list[ShopCategory]:
        stmt = (
            select(ShopCategory)
            .options(
                selectinload(ShopCategory.subcategories),
                selectinload(ShopCategory.parent),
            )
            .where(ShopCategory.shop_id == shop_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_subcategories(self, *, shop_id: int) -> list[ShopCategory]:
        stmt = (
            select(ShopCategory)
            .options(selectinload(ShopCategory.parent))
            .where(
                ShopCategory.shop_id == shop_id,
                ShopCategory.parent_id.isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_category_by_id(self, *, shop_id: int, category_id: int) -> ShopCategory | None:
        stmt = select(ShopCategory).where(
            ShopCategory.shop_id == shop_id,
            ShopCategory.id == category_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_items(self, *, shop_id: int) -> list[ShopItem]:
        stmt = (
            select(ShopItem)
            .options(selectinload(ShopItem.category).selectinload(ShopCategory.parent))
            .where(ShopItem.shop_id == shop_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_items_by_category(self, *, shop_id: int, category_id: int) -> list[ShopItem]:
        stmt = select(ShopItem).where(
            ShopItem.shop_id == shop_id,
            ShopItem.category_id == category_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_item_by_id(self, *, shop_id: int, item_id: int) -> ShopItem | None:
        stmt = select(ShopItem).where(
            ShopItem.shop_id == shop_id,
            ShopItem.id == item_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_category(
        self,
        *,
        shop_id: int,
        title: str,
        img: str,
        parent_id: int | None = None,
    ) -> ShopCategory:
        if parent_id is not None:
            parent = await self.get_category_by_id(shop_id=shop_id, category_id=parent_id)
            if not parent:
                raise ValueError("Parent category not found in this shop")

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

    async def create_item(
        self,
        *,
        shop_id: int,
        title: str,
        price: int,
        description: str | None,
        img: str,
        category_id: int,
    ) -> ShopItem:
        if price < 0:
            raise ValueError("Price must be non-negative")

        category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            raise ValueError("Category not found in this shop")

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

    async def update_category(
        self,
        *,
        shop_id: int,
        category_id: int,
        title: str | None = None,
        img: str | None = None,
        parent_id: int | None = None,
    ) -> ShopCategory | None:
        stmt = select(ShopCategory).where(
            ShopCategory.shop_id == shop_id,
            ShopCategory.id == category_id,
        )
        category = (await self.session.execute(stmt)).scalar_one_or_none()
        if not category:
            return None

        if parent_id is not None:
            if parent_id == category.id:
                raise ValueError("Category cannot be parent of itself")

            parent = await self.get_category_by_id(shop_id=shop_id, category_id=parent_id)
            if not parent:
                raise ValueError("Parent category not found in this shop")
            category.parent_id = parent_id

        if title is not None:
            category.title = title
        if img is not None:
            category.img = img

        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def update_item(
        self,
        *,
        shop_id: int,
        item_id: int,
        title: str | None = None,
        price: int | None = None,
        description: str | None = None,
        img: str | None = None,
        category_id: int | None = None,
    ) -> ShopItem | None:
        stmt = select(ShopItem).where(
            ShopItem.shop_id == shop_id,
            ShopItem.id == item_id,
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if not item:
            return None

        if title is not None:
            item.title = title

        if price is not None:
            if not isinstance(price, int) or price < 0:
                raise ValueError("Price must be a non-negative integer")
            item.price = price

        if description is not None:
            item.description = description

        if img is not None:
            item.img = img

        if category_id is not None:
            category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
            if not category:
                raise ValueError("Category not found in this shop")
            item.category_id = category_id

        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete_item(self, *, shop_id: int, item_id: int) -> bool:
        stmt = select(ShopItem).where(
            ShopItem.shop_id == shop_id,
            ShopItem.id == item_id,
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if not item:
            return False

        await self.session.delete(item)
        await self.session.flush()
        return True

    async def delete_category(self, *, shop_id: int, category_id: int) -> DeleteCategoryResult:
        stmt = select(ShopCategory).where(
            ShopCategory.shop_id == shop_id,
            ShopCategory.id == category_id,
        )
        category = (await self.session.execute(stmt)).scalar_one_or_none()
        if not category:
            return DeleteCategoryResult.NOT_FOUND

        has_item = await self.session.scalar(
            select(ShopItem.id)
            .where(ShopItem.shop_id == shop_id, ShopItem.category_id == category_id)
            .limit(1)
        )
        if has_item:
            return DeleteCategoryResult.HAS_ITEMS

        has_child = await self.session.scalar(
            select(ShopCategory.id)
            .where(ShopCategory.shop_id == shop_id, ShopCategory.parent_id == category_id)
            .limit(1)
        )
        if has_child:
            return DeleteCategoryResult.HAS_SUBCATEGORIES

        await self.session.delete(category)
        await self.session.flush()
        return DeleteCategoryResult.OK

    async def get_shop_by_id(self, shop_id: int) -> Shop | None:
        stmt = (
            select(Shop)
            .where(Shop.id == shop_id)
            .options(
                selectinload(Shop.payment_configs), 
                selectinload(Shop.ui_assets), 
            )
        )
        return await self.session.scalar(stmt)
