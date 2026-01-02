from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import Shop, ShopPage

router = APIRouter(tags=["pages"])

PageType = Literal[
    "faq",
    "reviews",
    "profile",
    "guarantees",
    "support",
    "main_menu",
    "shop_menu",

    "orders_menu",
    "order_item_menu",
    "transactions_menu",
    "transaction_item_menu",
    "promocode_menu",
    "promocode_error_menu",
    "promocode_success_menu",

    "topup_balance_menu",        
    "choose_payment_menu",    
    "pally_payment_menu",      
    "lava_payment_menu",       
    "success_payment_menu",  
]


class ShopPageOut(BaseModel):
    id: int
    shop_id: int
    page_type: str
    title: str
    content: str
    image: Optional[str] = None
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


class ShopPageCreateIn(BaseModel):
    shop_id: int
    page_type: PageType
    title: str = Field(default="", max_length=64)     
    content: str = Field(min_length=1)
    image: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True
    sort_order: int = 0


class ShopPageUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=64)  
    content: Optional[str] = Field(default=None, min_length=1)
    image: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


async def _ensure_shop(session: AsyncSession, shop_id: int) -> Shop:
    shop = await session.scalar(select(Shop).where(Shop.id == shop_id))
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


async def _ensure_page(session: AsyncSession, shop_id: int, page_id: int) -> ShopPage:
    page = await session.scalar(select(ShopPage).where(ShopPage.id == page_id, ShopPage.shop_id == shop_id))
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.get("", response_model=list[ShopPageOut])
async def list_pages(
    shop_id: int = Query(...),
    only_active: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, shop_id)

    stmt = select(ShopPage).where(ShopPage.shop_id == shop_id)
    if only_active:
        stmt = stmt.where(ShopPage.is_active.is_(True))

    stmt = stmt.order_by(ShopPage.sort_order.asc(), ShopPage.id.asc())
    pages = (await session.execute(stmt)).scalars().all()
    return pages


@router.get("/by-type", response_model=ShopPageOut)
async def get_page_by_type(
    shop_id: int = Query(...),
    page_type: PageType = Query(...),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, shop_id)

    page = await session.scalar(select(ShopPage).where(ShopPage.shop_id == shop_id, ShopPage.page_type == page_type))
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("", response_model=ShopPageOut)
async def create_page(
    payload: ShopPageCreateIn,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, payload.shop_id)

    page = ShopPage(
        shop_id=payload.shop_id,
        page_type=payload.page_type,
        title=payload.title or "",   
        content=payload.content,
        image=payload.image,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    session.add(page)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="This page_type already exists for this shop")

    await session.refresh(page)
    return page


@router.patch("/{page_id}", response_model=ShopPageOut)
async def update_page(
    page_id: int,
    shop_id: int = Query(...),
    payload: ShopPageUpdateIn = ...,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    page = await _ensure_page(session, shop_id, page_id)

    if payload.title is not None:
        page.title = payload.title

    if payload.content is not None:
        page.content = payload.content
    if payload.image is not None:
        page.image = payload.image
    if payload.is_active is not None:
        page.is_active = payload.is_active
    if payload.sort_order is not None:
        page.sort_order = payload.sort_order

    await session.commit()
    await session.refresh(page)
    return page


@router.delete("/{page_id}")
async def delete_page(
    page_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    page = await _ensure_page(session, shop_id, page_id)
    await session.delete(page)
    await session.commit()
    return {"ok": True}
