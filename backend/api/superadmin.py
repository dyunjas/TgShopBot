from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import Shop

router = APIRouter(tags=["superadmin"])


class ShopCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    bot_token: str = Field(..., min_length=1, max_length=2048)
    is_active: bool = True


class ShopUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    bot_token: str | None = Field(None, min_length=1, max_length=2048)
    is_active: bool | None = None


class ShopToggleIn(BaseModel):
    is_active: bool


@router.post("/shops")
async def create_shop(
    payload: ShopCreateIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    exists = await session.scalar(select(Shop).where(Shop.bot_token == payload.bot_token))
    if exists:
        raise HTTPException(status_code=400, detail="Такой токен уже используется другим магазином")

    shop = Shop(
        title=payload.title.strip(),
        bot_token=payload.bot_token.strip(),
        is_active=payload.is_active,
    )
    session.add(shop)
    await session.commit()
    await session.refresh(shop)

    return {"id": shop.id, "title": shop.title, "is_active": shop.is_active}


@router.get("/shops")
async def list_shops(
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shops = (await session.execute(select(Shop).order_by(Shop.id.asc()))).scalars().all()
    return [{"id": s.id, "title": s.title, "is_active": s.is_active, "bot_token": s.bot_token} for s in shops]


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

    if payload.bot_token is not None:
        new_token = payload.bot_token.strip()
        if new_token != shop.bot_token:
            exists = await session.scalar(select(Shop).where(Shop.bot_token == new_token))
            if exists:
                raise HTTPException(status_code=400, detail="Такой токен уже используется другим магазином")
            shop.bot_token = new_token

    if payload.title is not None:
        shop.title = payload.title.strip()

    if payload.is_active is not None:
        shop.is_active = payload.is_active

    await session.commit()
    await session.refresh(shop)
    return {"id": shop.id, "title": shop.title, "is_active": shop.is_active}


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
    return {"id": shop.id, "title": shop.title, "is_active": shop.is_active}


@router.post("/shops/{shop_id}/restart")
async def restart_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):

    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    return {"ok": True, "message": "Команда перезапуска отправлена", "shop_id": shop_id}


@router.delete("/shops/{shop_id}")
async def delete_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    await session.execute(delete(Shop).where(Shop.id == shop_id))
    await session.commit()
    return {"ok": True}
