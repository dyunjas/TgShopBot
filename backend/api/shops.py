from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import Shop

from backend.services.runtime import shop_bot_manager

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


@router.post("/shops")
async def create_shop(
    payload: ShopCreateIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    token = payload.bot_token.strip()
    title = payload.title.strip()

    exists = await session.scalar(select(Shop).where(Shop.bot_token == token))
    if exists:
        raise HTTPException(status_code=400, detail="Такой токен уже используется другим магазином")

    shop = Shop(
        title=title,
        bot_token=token,
        reviews_channel_id=int(payload.reviews_channel_id or 0),
        is_active=payload.is_active,
    )
    session.add(shop)
    await session.commit()
    await session.refresh(shop)

    if shop.is_active:
        await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)

    return {
        "id": shop.id,
        "title": shop.title,
        "is_active": shop.is_active,
        "bot_token": shop.bot_token,
        "reviews_channel_id": shop.reviews_channel_id,
    }


@router.get("/shops")
async def list_shops(
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shops = (await session.execute(select(Shop).order_by(Shop.id.asc()))).scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "is_active": s.is_active,
            "bot_token": s.bot_token,
            "reviews_channel_id": s.reviews_channel_id,
        }
        for s in shops
    ]


@router.patch("/shops/{shop_id}")
async def update_shop(
    shop_id: int,
    payload: ShopUpdateIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    old_token = shop.bot_token
    old_active = bool(shop.is_active)

    if payload.title is not None:
        shop.title = payload.title.strip()

    if payload.bot_token is not None:
        new_token = payload.bot_token.strip()
        if new_token != shop.bot_token:
            exists = await session.scalar(select(Shop).where(Shop.bot_token == new_token))
            if exists:
                raise HTTPException(status_code=400, detail="Такой токен уже используется другим магазином")
            shop.bot_token = new_token

    if payload.reviews_channel_id is not None:
        shop.reviews_channel_id = int(payload.reviews_channel_id)

    if payload.is_active is not None:
        shop.is_active = bool(payload.is_active)

    await session.commit()
    await session.refresh(shop)

    if old_active and not shop.is_active:
        await shop_bot_manager.stop_shop(shop_id)
        return {
            "id": shop.id,
            "title": shop.title,
            "is_active": shop.is_active,
            "bot_token": shop.bot_token,
            "reviews_channel_id": shop.reviews_channel_id,
            "message": "Магазин выключен",
        }

    if (not old_active) and shop.is_active:
        await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
        return {
            "id": shop.id,
            "title": shop.title,
            "is_active": shop.is_active,
            "bot_token": shop.bot_token,
            "reviews_channel_id": shop.reviews_channel_id,
            "message": "Магазин включён",
        }

    token_changed = payload.bot_token is not None and shop.bot_token != old_token
    if shop.is_active and token_changed:
        await shop_bot_manager.stop_shop(shop_id)
        await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
        return {
            "id": shop.id,
            "title": shop.title,
            "is_active": shop.is_active,
            "bot_token": shop.bot_token,
            "reviews_channel_id": shop.reviews_channel_id,
            "message": "Токен обновлён, бот перезапущен",
        }

    return {
        "id": shop.id,
        "title": shop.title,
        "is_active": shop.is_active,
        "bot_token": shop.bot_token,
        "reviews_channel_id": shop.reviews_channel_id,
        "message": "Изменения сохранены",
    }


@router.post("/shops/{shop_id}/toggle")
async def toggle_shop(
    shop_id: int,
    payload: ShopToggleIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    shop.is_active = bool(payload.is_active)
    await session.commit()
    await session.refresh(shop)

    if shop.is_active:
        await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
        return {
            "id": shop.id,
            "title": shop.title,
            "is_active": shop.is_active,
            "bot_token": shop.bot_token,
            "reviews_channel_id": shop.reviews_channel_id,
            "message": "Магазин запущен",
        }

    await shop_bot_manager.stop_shop(shop.id)
    return {
        "id": shop.id,
        "title": shop.title,
        "is_active": shop.is_active,
        "bot_token": shop.bot_token,
        "reviews_channel_id": shop.reviews_channel_id,
        "message": "Магазин остановлен",
    }


@router.post("/shops/{shop_id}/restart")
async def restart_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    if not shop.is_active:
        raise HTTPException(status_code=400, detail="Магазин выключен. Сначала включите его.")

    await shop_bot_manager.stop_shop(shop.id)
    await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)

    return {"ok": True, "message": "Магазин перезапущен"}


@router.delete("/shops/{shop_id}")
async def delete_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    await shop_bot_manager.stop_shop(shop_id)

    await session.execute(delete(Shop).where(Shop.id == shop_id))
    await session.commit()

    return {"ok": True, "message": "Магазин удалён"}
