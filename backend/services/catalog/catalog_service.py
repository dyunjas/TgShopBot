from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ShopCategory, ShopItem
from backend.repositories.category_repository import CategoryRepository, DeleteCategoryResult, UNSET
from backend.repositories.item_repository import ItemRepository
from backend.repositories.shop_read_repository import ShopReadRepository


@dataclass
class CatalogService:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.shops = ShopReadRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.items = ItemRepository(self.session)

    async def ensure_shop(self, shop_id: int) -> None:
        shop = await self.shops.get_by_id(shop_id=shop_id)
        if not shop:
            raise ValueError("Shop not found")

    async def list_categories(self, *, shop_id: int, parent_id: int | None = None) -> list[ShopCategory]:
        await self.ensure_shop(shop_id)
        return await self.categories.list(shop_id=shop_id, parent_id=parent_id)

    async def create_category(
        self,
        *,
        shop_id: int,
        title: str,
        img: str,
        parent_id: int | None = None,
    ) -> ShopCategory:
        await self.ensure_shop(shop_id)

        if parent_id is not None:
            parent = await self.categories.get_by_id(shop_id=shop_id, category_id=parent_id)
            if not parent:
                raise ValueError("Parent category not found in this shop")

        return await self.categories.create(
            shop_id=shop_id,
            title=title,
            img=img,
            parent_id=parent_id,
        )

    async def update_category(
        self,
        *,
        shop_id: int,
        category_id: int,
        data: dict,
    ) -> ShopCategory | None:
        await self.ensure_shop(shop_id)

        category = await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            return None

        parent_id = data.get("parent_id", UNSET)
        if parent_id is not UNSET:
            if parent_id == category_id:
                raise ValueError("Category cannot be parent of itself")

            if parent_id is not None:
                parent = await self.categories.get_by_id(shop_id=shop_id, category_id=parent_id)
                if not parent:
                    raise ValueError("Parent category not found in this shop")

        return await self.categories.update(
            shop_id=shop_id,
            category_id=category_id,
            title=data.get("title", UNSET),
            img=data.get("img", UNSET),
            parent_id=parent_id,
        )

    async def delete_category(self, *, shop_id: int, category_id: int) -> DeleteCategoryResult:
        await self.ensure_shop(shop_id)

        category = await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            return DeleteCategoryResult.NOT_FOUND

        if await self.categories.has_items(shop_id=shop_id, category_id=category_id):
            return DeleteCategoryResult.HAS_ITEMS

        if await self.categories.has_children(shop_id=shop_id, category_id=category_id):
            return DeleteCategoryResult.HAS_SUBCATEGORIES

        await self.categories.delete(category)
        return DeleteCategoryResult.OK

    async def list_items(self, *, shop_id: int, category_id: int | None = None) -> list[ShopItem]:
        await self.ensure_shop(shop_id)

        if category_id is not None:
            category = await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)
            if not category:
                raise ValueError("Category not found")

        return await self.items.list(shop_id=shop_id, category_id=category_id)

    async def get_item(self, *, shop_id: int, item_id: int) -> ShopItem | None:
        await self.ensure_shop(shop_id)
        return await self.items.get_by_id(shop_id=shop_id, item_id=item_id)

    async def create_item(
        self,
        *,
        shop_id: int,
        category_id: int,
        title: str,
        price: int,
        description: str | None,
        img: str,
    ) -> ShopItem:
        await self.ensure_shop(shop_id)

        if price < 0:
            raise ValueError("Price must be non-negative")

        category = await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            raise ValueError("Category not found in this shop")

        return await self.items.create(
            shop_id=shop_id,
            category_id=category_id,
            title=title,
            price=price,
            description=description,
            img=img,
        )

    async def update_item(self, *, shop_id: int, item_id: int, data: dict) -> ShopItem | None:
        await self.ensure_shop(shop_id)

        item = await self.items.get_by_id(shop_id=shop_id, item_id=item_id)
        if not item:
            return None

        price = data.get("price", UNSET)
        if price is not UNSET:
            if not isinstance(price, int) or price < 0:
                raise ValueError("Price must be a non-negative integer")

        category_id = data.get("category_id", UNSET)
        if category_id is not UNSET:
            category = await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)
            if not category:
                raise ValueError("Category not found in this shop")

        return await self.items.update(
            shop_id=shop_id,
            item_id=item_id,
            title=data.get("title", UNSET),
            price=price,
            description=data.get("description", UNSET),
            img=data.get("img", UNSET),
            category_id=category_id,
        )

    async def delete_item(self, *, shop_id: int, item_id: int) -> bool:
        await self.ensure_shop(shop_id)

        item = await self.items.get_by_id(shop_id=shop_id, item_id=item_id)
        if not item:
            return False

        await self.items.delete(item)
        return True

