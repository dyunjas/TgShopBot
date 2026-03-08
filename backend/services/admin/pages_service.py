from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Shop, ShopPage


@dataclass
class PagesService:
    session: AsyncSession

    async def ensure_shop(self, shop_id: int) -> None:
        shop = await self.session.scalar(select(Shop).where(Shop.id == shop_id))
        if not shop:
            raise LookupError("Shop not found")

    async def ensure_page(self, *, shop_id: int, page_id: int) -> ShopPage:
        page = await self.session.scalar(
            select(ShopPage).where(ShopPage.id == page_id, ShopPage.shop_id == shop_id)
        )
        if not page:
            raise LookupError("Page not found")
        return page

    async def list_pages(self, *, shop_id: int, only_active: bool) -> list[ShopPage]:
        await self.ensure_shop(shop_id)
        stmt = select(ShopPage).where(ShopPage.shop_id == shop_id)
        if only_active:
            stmt = stmt.where(ShopPage.is_active.is_(True))
        stmt = stmt.order_by(ShopPage.sort_order.asc(), ShopPage.id.asc())
        return (await self.session.execute(stmt)).scalars().all()

    async def get_page_by_type(self, *, shop_id: int, page_type: str) -> ShopPage:
        await self.ensure_shop(shop_id)
        page = await self.session.scalar(
            select(ShopPage).where(ShopPage.shop_id == shop_id, ShopPage.page_type == page_type)
        )
        if not page:
            raise LookupError("Page not found")
        return page

    async def create_page(
        self,
        *,
        shop_id: int,
        page_type: str,
        title: str,
        content: str,
        image: str | None,
        is_active: bool,
        sort_order: int,
    ) -> ShopPage:
        await self.ensure_shop(shop_id)
        page = ShopPage(
            shop_id=shop_id,
            page_type=page_type,
            title=title or "",
            content=content,
            image=image,
            is_active=is_active,
            sort_order=sort_order,
        )
        self.session.add(page)
        await self.session.flush()
        await self.session.refresh(page)
        return page

    async def update_page(
        self,
        *,
        page_id: int,
        shop_id: int,
        title: str | None = None,
        content: str | None = None,
        image: str | None = None,
        is_active: bool | None = None,
        sort_order: int | None = None,
    ) -> ShopPage:
        page = await self.ensure_page(shop_id=shop_id, page_id=page_id)

        if title is not None:
            page.title = title
        if content is not None:
            page.content = content
        if image is not None:
            page.image = image
        if is_active is not None:
            page.is_active = is_active
        if sort_order is not None:
            page.sort_order = sort_order

        await self.session.flush()
        await self.session.refresh(page)
        return page

    async def delete_page(self, *, page_id: int, shop_id: int) -> dict:
        page = await self.ensure_page(shop_id=shop_id, page_id=page_id)
        await self.session.delete(page)
        await self.session.flush()
        return {"ok": True}
