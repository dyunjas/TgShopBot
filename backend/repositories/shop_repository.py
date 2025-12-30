from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ShopCategory, ShopItem

from sqlalchemy.orm import selectinload

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_categories(self, parent_id: int | None = None) -> list[ShopCategory]:
        stmt = select(ShopCategory).options(selectinload(ShopCategory.parent)).where(ShopCategory.parent_id == parent_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_items(self) -> list[ShopItem]:
        stmt = select(ShopItem).options(
            selectinload(ShopItem.category).selectinload(ShopCategory.parent)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_items_by_category(self, category_id: int) -> list[ShopItem]:
        stmt = select(ShopItem).where(ShopItem.category_id == category_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_item_by_id(self, item_id: int) -> ShopItem | None:
        stmt = select(ShopItem).where(ShopItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_category_by_id(self, category_id: int) -> ShopCategory | None:
        stmt = select(ShopCategory).where(ShopCategory.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_category(self, title: str, img: str, parent_id: int | None = None) -> ShopCategory:
        category = ShopCategory(
            title=title,
            img=img,
            parent_id=parent_id
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def create_item(
            self, 
            title: str,
            price: int,
            description: str,
            img: str,
            category_id: int
    ) -> ShopItem:
        item = ShopItem(
            title=title,
            price=price,
            description=description,
            img=img,
            category_id=category_id
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def get_all_categories(self) -> list[ShopCategory]:
        stmt = select(ShopCategory).options(
            selectinload(ShopCategory.subcategories),
            selectinload(ShopCategory.parent)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def delete_item(self, item_id: int) -> None:
        stmt = select(ShopItem).where(ShopItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()

    async def delete_category(self, category_id: int) -> bool:
        stmt = select(ShopCategory).options(
            selectinload(ShopCategory.items),
            selectinload(ShopCategory.subcategories)
        ).where(ShopCategory.id == category_id)

        result = await self.session.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            return False

        if category.items or category.subcategories:
            return False

        await self.session.delete(category)
        await self.session.commit()
        return True
    
    async def get_subcategories(self) -> list[ShopCategory]:
        stmt = select(ShopCategory).options(
            selectinload(ShopCategory.parent)
        ).where(ShopCategory.parent_id.isnot(None))
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_category(
            self,
            cateory_id: int, 
            *,
            title: str | None = None,
            img: str | None = None,
            parent_id: int | None = None,
    ) -> ShopCategory | None:
        
        stmt = select(ShopCategory).where(ShopCategory.id == cateory_id)
        result = await self.session.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            return None
        
        if title is not None:
            category.title = title
        if img is not None:
            category.img = img
        if parent_id is not None:
            category.parent_id = parent_id

        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update_item(
            self,
            item_id: int,
            *,
            title: str | None = None,
            price: int | None = None,
            description: str | None = None,
            img: str | None = None,
            category_id: int | None = None
    ) -> ShopItem | None:
        
        stmt = select(ShopItem).where(ShopItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return None
        
        if title is not None:
            item.title = title
        if price is not None:
            if not isinstance(price, int) or price < 0:
                raise ValueError("Price must be a non-negative integer")
        if description is not None:
            item.description = description
        if img is not None:
            item.img = img
        if category_id is not None:
            item.category_id = category_id

        await self.session.commit()
        await self.session.refresh(item)
        return item

