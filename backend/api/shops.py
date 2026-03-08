from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.services.admin import ShopsService

router = APIRouter(tags=["superadmin"])


class ShopCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    bot_token: str = Field(..., min_length=1, max_length=2048)
    reviews_channel_id: int | None = None
    is_active: bool = True


class ShopUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    bot_token: str | None = Field(None, min_length=1, max_length=2048)
    reviews_channel_id: int | None = None
    is_active: bool | None = None


class ShopToggleIn(BaseModel):
    is_active: bool


def get_service(session: AsyncSession = Depends(get_session)) -> ShopsService:
    return ShopsService(session)


@router.post("/shops")
async def create_shop(
    payload: ShopCreateIn,
    session: AsyncSession = Depends(get_session),
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.create_shop(
            title=payload.title,
            bot_token=payload.bot_token,
            reviews_channel_id=payload.reviews_channel_id,
            is_active=payload.is_active,
        )
        await session.commit()
        return result
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shops")
async def list_shops(
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    return await service.list_shops()


@router.patch("/shops/{shop_id}")
async def update_shop(
    shop_id: int,
    payload: ShopUpdateIn,
    session: AsyncSession = Depends(get_session),
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.update_shop(
            shop_id=shop_id,
            title=payload.title,
            bot_token=payload.bot_token,
            reviews_channel_id=payload.reviews_channel_id,
            is_active=payload.is_active,
        )
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shops/{shop_id}/toggle")
async def toggle_shop(
    shop_id: int,
    payload: ShopToggleIn,
    session: AsyncSession = Depends(get_session),
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.toggle_shop(shop_id=shop_id, is_active=payload.is_active)
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/shops/{shop_id}/restart")
async def restart_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.restart_shop(shop_id=shop_id)
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/shops/{shop_id}")
async def delete_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    service: ShopsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.delete_shop(shop_id=shop_id)
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
