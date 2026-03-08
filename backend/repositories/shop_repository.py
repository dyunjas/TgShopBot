from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .category_repository import CategoryRepository, DeleteCategoryResult, UNSET
from .item_repository import ItemRepository
from .shop_read_repository import ShopReadRepository


class ShopRepository:
    """Backward-compatible facade used by bot handlers.

    New code should use specialized repositories + services.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.shops = ShopReadRepository(session)
        self.categories = CategoryRepository(session)
        self.items = ItemRepository(session)

    async def get_categories(self, *, shop_id: int, parent_id: int | None = None):
        return await self.categories.list(shop_id=shop_id, parent_id=parent_id)

    async def get_all_categories(self, *, shop_id: int):
        roots = await self.categories.list(shop_id=shop_id, parent_id=None)
        all_categories = list(roots)
        queue = [c.id for c in roots]

        while queue:
            current_parent = queue.pop(0)
            children = await self.categories.list(shop_id=shop_id, parent_id=current_parent)
            all_categories.extend(children)
            queue.extend(c.id for c in children)

        return all_categories

    async def get_subcategories(self, *, shop_id: int):
        all_categories = await self.get_all_categories(shop_id=shop_id)
        return [c for c in all_categories if c.parent_id is not None]

    async def get_category_by_id(self, *, shop_id: int, category_id: int):
        return await self.categories.get_by_id(shop_id=shop_id, category_id=category_id)

    async def get_items(self, *, shop_id: int):
        return await self.items.list(shop_id=shop_id)

    async def get_items_by_category(self, *, shop_id: int, category_id: int):
        return await self.items.list(shop_id=shop_id, category_id=category_id)

    async def get_item_by_id(self, *, shop_id: int, item_id: int):
        return await self.items.get_by_id(shop_id=shop_id, item_id=item_id)

    async def create_category(self, *, shop_id: int, title: str, img: str, parent_id: int | None = None):
        if parent_id is not None:
            parent = await self.get_category_by_id(shop_id=shop_id, category_id=parent_id)
            if not parent:
                raise ValueError("Parent category not found in this shop")
        return await self.categories.create(shop_id=shop_id, title=title, img=img, parent_id=parent_id)

    async def create_item(
        self,
        *,
        shop_id: int,
        title: str,
        price: int,
        description: str | None,
        img: str,
        category_id: int,
    ):
        if price < 0:
            raise ValueError("Price must be non-negative")

        category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            raise ValueError("Category not found in this shop")

        return await self.items.create(
            shop_id=shop_id,
            title=title,
            price=price,
            description=description,
            img=img,
            category_id=category_id,
        )

    async def update_category(
        self,
        *,
        shop_id: int,
        category_id: int,
        title: str | None = None,
        img: str | None = None,
        parent_id: int | None | object = UNSET,
    ):
        category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            return None

        if parent_id is not UNSET:
            if parent_id == category.id:
                raise ValueError("Category cannot be parent of itself")

            if parent_id is not None:
                parent = await self.get_category_by_id(shop_id=shop_id, category_id=parent_id)
                if not parent:
                    raise ValueError("Parent category not found in this shop")

        return await self.categories.update(
            shop_id=shop_id,
            category_id=category_id,
            title=title if title is not None else UNSET,
            img=img if img is not None else UNSET,
            parent_id=parent_id,
        )

    async def update_item(
        self,
        *,
        shop_id: int,
        item_id: int,
        title: str | None = None,
        price: int | None = None,
        description: str | None | object = UNSET,
        img: str | None = None,
        category_id: int | None = None,
    ):
        item = await self.get_item_by_id(shop_id=shop_id, item_id=item_id)
        if not item:
            return None

        if price is not None and price < 0:
            raise ValueError("Price must be a non-negative integer")

        if category_id is not None:
            category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
            if not category:
                raise ValueError("Category not found in this shop")

        return await self.items.update(
            shop_id=shop_id,
            item_id=item_id,
            title=title if title is not None else UNSET,
            price=price if price is not None else UNSET,
            description=description,
            img=img if img is not None else UNSET,
            category_id=category_id if category_id is not None else UNSET,
        )

    async def delete_item(self, *, shop_id: int, item_id: int) -> bool:
        item = await self.get_item_by_id(shop_id=shop_id, item_id=item_id)
        if not item:
            return False
        await self.items.delete(item)
        return True

    async def delete_category(self, *, shop_id: int, category_id: int) -> DeleteCategoryResult:
        category = await self.get_category_by_id(shop_id=shop_id, category_id=category_id)
        if not category:
            return DeleteCategoryResult.NOT_FOUND

        if await self.categories.has_items(shop_id=shop_id, category_id=category_id):
            return DeleteCategoryResult.HAS_ITEMS

        if await self.categories.has_children(shop_id=shop_id, category_id=category_id):
            return DeleteCategoryResult.HAS_SUBCATEGORIES

        await self.categories.delete(category)
        return DeleteCategoryResult.OK

    async def get_shop_by_id(self, shop_id: int):
        return await self.shops.get_by_id(shop_id=shop_id)

