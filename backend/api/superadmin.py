from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import Shop, AdminUser

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


class OperatorCreateIn(BaseModel):
    tg_id: int = Field(..., gt=0)
    username: str | None = Field(None, max_length=64)


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
        reviews_channel_id=int(payload.reviews_channel_id or 0),
        is_active=payload.is_active,
    )
    session.add(shop)
    await session.commit()
    await session.refresh(shop)

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

    if payload.bot_token is not None:
        new_token = payload.bot_token.strip()
        if new_token != shop.bot_token:
            exists = await session.scalar(select(Shop).where(Shop.bot_token == new_token))
            if exists:
                raise HTTPException(status_code=400, detail="Такой токен уже используется другим магазином")
            shop.bot_token = new_token

    if payload.title is not None:
        shop.title = payload.title.strip()

    if payload.reviews_channel_id is not None:
        shop.reviews_channel_id = int(payload.reviews_channel_id)

    if payload.is_active is not None:
        shop.is_active = payload.is_active

    await session.commit()
    await session.refresh(shop)
    return {
        "id": shop.id,
        "title": shop.title,
        "is_active": shop.is_active,
        "bot_token": shop.bot_token,
        "reviews_channel_id": shop.reviews_channel_id,
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


@router.get("/operators")
async def list_operators(
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    stmt = (
        select(AdminUser)
        .where(AdminUser.role.in_(("operator", "superadmin")))
        .order_by(AdminUser.role.desc(), AdminUser.id.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": a.id,
            "tg_id": a.tg_id,
            "username": a.username,
            "role": a.role,
            "balance": a.balance,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


@router.post("/operators")
async def create_or_assign_operator(
    payload: OperatorCreateIn,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    existing = await session.scalar(select(AdminUser).where(AdminUser.tg_id == payload.tg_id))
    if existing:
        if existing.role == "superadmin":
            raise HTTPException(status_code=400, detail="Нельзя изменять роль супер-админа через этот раздел")
        existing.role = "operator"
        if payload.username is not None:
            existing.username = payload.username.strip() or None
        await session.commit()
        await session.refresh(existing)
        return {
            "id": existing.id,
            "tg_id": existing.tg_id,
            "username": existing.username,
            "role": existing.role,
            "balance": existing.balance,
        }

    admin = AdminUser(
        tg_id=payload.tg_id,
        username=(payload.username.strip() if payload.username else None),
        role="operator",
        balance=0,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return {
        "id": admin.id,
        "tg_id": admin.tg_id,
        "username": admin.username,
        "role": admin.role,
        "balance": admin.balance,
    }


@router.delete("/operators/{admin_id}")
async def delete_operator(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    admin = await session.get(AdminUser, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    if admin.role != "operator":
        raise HTTPException(status_code=400, detail="Удалять можно только операторов")

    await session.execute(delete(AdminUser).where(AdminUser.id == admin_id))
    await session.commit()
    return {"ok": True}
