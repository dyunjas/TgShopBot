from __future__ import annotations

import asyncio
from typing import Literal, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role

from backend.database.models import Shop, ShopUser, ShopCategory, ShopItem 
from backend.repositories.user_repository import ShopUserRepository  

router = APIRouter(tags=["broadcast"])


class AudienceFilterIn(BaseModel):
    mode: Literal["all", "by_ids", "segment"] = "all"

    tg_ids: list[int] | None = None

    lang: str | None = Field(None, min_length=2, max_length=8)
    min_balance: int | None = Field(None, ge=0)
    max_balance: int | None = Field(None, ge=0)
    min_orders: int | None = Field(None, ge=0)
    max_orders: int | None = Field(None, ge=0)

    limit: int | None = Field(None, ge=1, le=50000)


class ButtonTargetIn(BaseModel):
    target_type: Literal["category", "item", "support", "main_menu"]
    target_id: int | None = None


class ResolveButtonIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=64)
    target: ButtonTargetIn


class ResolvedButtonOut(BaseModel):
    text: str
    callback_data: str
    meta: dict = Field(default_factory=dict)


class BroadcastButtonIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=64)
    callback_data: str = Field(..., min_length=1, max_length=64)


class BroadcastCreateIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    photo_id: str | None = Field(None, min_length=1, max_length=2048)

    audience: AudienceFilterIn = Field(default_factory=AudienceFilterIn)

    buttons: list[BroadcastButtonIn] = Field(default_factory=list)
    buttons_per_row: int = Field(2, ge=1, le=4)

    delay_sec: float = Field(0.05, ge=0.0, le=3.0)


class BroadcastResultOut(BaseModel):
    ok: bool
    shop_id: int
    total_targeted: int
    sent_ok: int
    sent_failed: int


def build_keyboard(buttons: Sequence[BroadcastButtonIn], per_row: int) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None

    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for b in buttons:
        if not b.callback_data:
            raise HTTPException(status_code=400, detail="button.callback_data обязателен")
        btn = InlineKeyboardButton(text=b.text, callback_data=b.callback_data)

        row.append(btn)
        if len(row) >= per_row:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def get_shop_bot(session: AsyncSession, shop_id: int) -> Bot:
    shop = await session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    if not shop.is_active:
        raise HTTPException(status_code=400, detail="Магазин выключен")
    if not shop.bot_token:
        raise HTTPException(status_code=400, detail="У магазина нет bot_token")
    return Bot(token=shop.bot_token)


async def select_targets(session: AsyncSession, shop_id: int, audience: AudienceFilterIn) -> list[int]:
    if audience.mode == "all":
        stmt = select(ShopUser.tg_id).where(ShopUser.shop_id == shop_id)
        if audience.limit:
            stmt = stmt.limit(audience.limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    if audience.mode == "by_ids":
        if not audience.tg_ids:
            return []
        stmt = select(ShopUser.tg_id).where(
            ShopUser.shop_id == shop_id,
            ShopUser.tg_id.in_(audience.tg_ids),
        )
        res = await session.execute(stmt)
        ids = list(res.scalars().all())
        if audience.limit:
            ids = ids[: audience.limit]
        return ids

    if audience.mode == "segment":
        stmt = select(ShopUser.tg_id).where(ShopUser.shop_id == shop_id)

        if audience.lang is not None:
            stmt = stmt.where(ShopUser.lang == audience.lang)

        if audience.min_balance is not None:
            stmt = stmt.where(ShopUser.balance >= audience.min_balance)
        if audience.max_balance is not None:
            stmt = stmt.where(ShopUser.balance <= audience.max_balance)

        if audience.min_orders is not None:
            stmt = stmt.where(ShopUser.orders_amount >= audience.min_orders)
        if audience.max_orders is not None:
            stmt = stmt.where(ShopUser.orders_amount <= audience.max_orders)

        if audience.limit:
            stmt = stmt.limit(audience.limit)

        res = await session.execute(stmt)
        return list(res.scalars().all())

    raise HTTPException(status_code=400, detail="Некорректный audience.mode")


@router.get("/shops/{shop_id}/targets/categories")
async def list_categories(
    shop_id: int,
    q: str | None = Query(None),
    parent_id: int | None = Query(None),
    limit: int = Query(80, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    stmt = select(ShopCategory).where(ShopCategory.shop_id == shop_id)

    if parent_id is None:
        stmt = stmt.where(ShopCategory.parent_id.is_(None))
    else:
        stmt = stmt.where(ShopCategory.parent_id == parent_id)

    if q:
        stmt = stmt.where(ShopCategory.title.ilike(f"%{q}%"))

    stmt = stmt.order_by(ShopCategory.id.desc()).limit(limit)
    cats = (await session.execute(stmt)).scalars().all()

    return [{"id": c.id, "title": c.title, "parent_id": c.parent_id} for c in cats]


@router.get("/shops/{shop_id}/targets/items")
async def list_items(
    shop_id: int,
    category_id: int | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(80, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    stmt = select(ShopItem).where(ShopItem.shop_id == shop_id)

    if category_id is not None:
        stmt = stmt.where(ShopItem.category_id == category_id)

    if q:
        stmt = stmt.where(ShopItem.title.ilike(f"%{q}%"))

    stmt = stmt.order_by(ShopItem.id.desc()).limit(limit)
    items = (await session.execute(stmt)).scalars().all()

    out = []
    for it in items:
        out.append(
            {
                "id": it.id,
                "title": getattr(it, "title", f"Item {it.id}"),
                "category_id": getattr(it, "category_id", None),
                "price": getattr(it, "price", None),
            }
        )
    return out


@router.post("/shops/{shop_id}/buttons/resolve", response_model=ResolvedButtonOut)
async def resolve_button(
    shop_id: int,
    payload: ResolveButtonIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    t = payload.target

    if t.target_type in ("support", "main_menu"):
        return ResolvedButtonOut(
            text=payload.text,
            callback_data=t.target_type,  
            meta={"target_type": t.target_type},
        )

    if t.target_type == "category":
        if not t.target_id:
            raise HTTPException(status_code=400, detail="target_id обязателен для category")
        return ResolvedButtonOut(
            text=payload.text,
            callback_data=f"category:{t.target_id}",
            meta={"target_type": "category", "id": t.target_id},
        )

    if t.target_type == "item":
        if not t.target_id:
            raise HTTPException(status_code=400, detail="target_id обязателен для item")
        return ResolvedButtonOut(
            text=payload.text,
            callback_data=f"item:{t.target_id}",
            meta={"target_type": "item", "id": t.target_id},
        )

    raise HTTPException(status_code=400, detail="Некорректный target_type")



@router.post("/shops/{shop_id}/send", response_model=BroadcastResultOut)
async def send_broadcast(
    shop_id: int,
    payload: BroadcastCreateIn,
    session: AsyncSession = Depends(get_session),
    current: CurrentAdmin = Depends(require_role("superadmin")),
):
    bot = await get_shop_bot(session, shop_id)
    kb = build_keyboard(payload.buttons, payload.buttons_per_row)

    repo = ShopUserRepository(session)
    tg_ids = await select_targets(session, shop_id, payload.audience)
    total = len(tg_ids)

    if total == 0:
        await bot.session.close()
        return BroadcastResultOut(ok=True, shop_id=shop_id, total_targeted=0, sent_ok=0, sent_failed=0)

    sent_ok = 0
    sent_failed = 0

    for tg_id in tg_ids:
        try:
            await repo.send_safe_message(
                bot=bot,
                user_id=tg_id,
                photo_id=payload.photo_id,
                text=payload.text,
                reply_markup=kb,
            )
            sent_ok += 1
        except Exception:
            sent_failed += 1

        if payload.delay_sec > 0:
            await asyncio.sleep(payload.delay_sec)

    await bot.session.close()

    return BroadcastResultOut(
        ok=True,
        shop_id=shop_id,
        total_targeted=total,
        sent_ok=sent_ok,
        sent_failed=sent_failed,
    )
