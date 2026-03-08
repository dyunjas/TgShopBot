from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.services.admin import PagesService

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


def get_service(session: AsyncSession = Depends(get_session)) -> PagesService:
    return PagesService(session)


@router.get("", response_model=list[ShopPageOut])
async def list_pages(
    shop_id: int = Query(...),
    only_active: bool = Query(default=False),
    service: PagesService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.list_pages(shop_id=shop_id, only_active=only_active)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/by-type", response_model=ShopPageOut)
async def get_page_by_type(
    shop_id: int = Query(...),
    page_type: PageType = Query(...),
    service: PagesService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.get_page_by_type(shop_id=shop_id, page_type=page_type)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ShopPageOut)
async def create_page(
    payload: ShopPageCreateIn,
    session: AsyncSession = Depends(get_session),
    service: PagesService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        page = await service.create_page(
            shop_id=payload.shop_id,
            page_type=payload.page_type,
            title=payload.title,
            content=payload.content,
            image=payload.image,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
        await session.commit()
        return page
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="This page_type already exists for this shop")


@router.patch("/{page_id}", response_model=ShopPageOut)
async def update_page(
    page_id: int,
    shop_id: int = Query(...),
    payload: ShopPageUpdateIn = ...,
    session: AsyncSession = Depends(get_session),
    service: PagesService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        page = await service.update_page(
            page_id=page_id,
            shop_id=shop_id,
            title=payload.title,
            content=payload.content,
            image=payload.image,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
        await session.commit()
        return page
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{page_id}")
async def delete_page(
    page_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: PagesService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.delete_page(page_id=page_id, shop_id=shop_id)
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
