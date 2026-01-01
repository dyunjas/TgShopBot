from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ShopPage


class ShopPageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_page(
        self,
        *,
        shop_id: int,
        page_type: str,
        only_active: bool = True,
    ) -> ShopPage | None:

        stmt = select(ShopPage).where(
            ShopPage.shop_id == shop_id,
            ShopPage.page_type == page_type,
        )

        if only_active:
            stmt = stmt.where(ShopPage.is_active.is_(True))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pages(
        self,
        *,
        shop_id: int,
        only_active: bool = True,
    ) -> list[ShopPage]:

        stmt = select(ShopPage).where(ShopPage.shop_id == shop_id)

        if only_active:
            stmt = stmt.where(ShopPage.is_active.is_(True))

        stmt = stmt.order_by(ShopPage.sort_order.asc())

        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def create_page(
        self,
        *,
        shop_id: int,
        page_type: str,
        title: str,
        content: str,
        image: str | None = None,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> ShopPage:
        page = ShopPage(
            shop_id=shop_id,
            page_type=page_type,
            title=title,
            content=content,
            image=image,
            sort_order=sort_order,
            is_active=is_active,
        )
        self.session.add(page)
        await self.session.flush()
        await self.session.refresh(page)
        return page

    async def update_page(
        self,
        *,
        shop_id: int,
        page_type: str,
        title: str | None = None,
        content: str | None = None,
        image: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
    ) -> ShopPage | None:
        stmt = select(ShopPage).where(
            ShopPage.shop_id == shop_id,
            ShopPage.page_type == page_type,
        ).with_for_update()

        page = (await self.session.execute(stmt)).scalar_one_or_none()
        if not page:
            return None

        if title is not None:
            page.title = title
        if content is not None:
            page.content = content
        if image is not None:
            page.image = image
        if sort_order is not None:
            page.sort_order = sort_order
        if is_active is not None:
            page.is_active = is_active

        await self.session.flush()
        await self.session.refresh(page)
        return page


    async def delete_page(
        self,
        *,
        shop_id: int,
        page_type: str,
    ) -> bool:
        stmt = select(ShopPage).where(
            ShopPage.shop_id == shop_id,
            ShopPage.page_type == page_type,
        )
        page = (await self.session.execute(stmt)).scalar_one_or_none()
        if not page:
            return False

        await self.session.delete(page)
        await self.session.flush()
        return True
