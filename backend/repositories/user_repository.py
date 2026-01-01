from __future__ import annotations

import asyncio
from typing import Iterable

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ShopUser


class ShopUserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, *, shop_id: int, tg_id: int, username: str | None) -> ShopUser:
        user = ShopUser(
            shop_id=shop_id,
            tg_id=tg_id,
            username=username,
            balance=0,
            lang="ru",
            orders_amount=0,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_user(self, *, shop_id: int, tg_id: int) -> ShopUser | None:
        stmt = select(ShopUser).where(
            ShopUser.shop_id == shop_id,
            ShopUser.tg_id == tg_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def update_username(self, *, shop_id: int, tg_id: int, new_username: str | None) -> None:
        stmt = (
            select(ShopUser)
            .where(ShopUser.shop_id == shop_id, ShopUser.tg_id == tg_id)
            .with_for_update()
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            return
        user.username = new_username
        await self.session.flush()

    async def increase_balance(self, *, shop_id: int, tg_id: int, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be >= 0")

        stmt = (
            select(ShopUser)
            .where(ShopUser.shop_id == shop_id, ShopUser.tg_id == tg_id)
            .with_for_update()
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise ValueError(f"User with tg_id={tg_id} not found in shop_id={shop_id}")

        user.balance += amount
        await self.session.flush()
        await self.session.refresh(user)
        return user.balance

    async def decrease_balance(self, *, shop_id: int, tg_id: int, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be >= 0")

        stmt = (
            select(ShopUser)
            .where(ShopUser.shop_id == shop_id, ShopUser.tg_id == tg_id)
            .with_for_update()
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise ValueError(f"User with tg_id={tg_id} not found in shop_id={shop_id}")

        user.balance -= amount
        await self.session.flush()
        await self.session.refresh(user)
        return user.balance

    async def increase_orders_amount(self, *, shop_id: int, tg_id: int, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be >= 0")

        stmt = (
            select(ShopUser)
            .where(ShopUser.shop_id == shop_id, ShopUser.tg_id == tg_id)
            .with_for_update()
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise ValueError(f"User with tg_id={tg_id} not found in shop_id={shop_id}")

        user.orders_amount += amount
        await self.session.flush()
        await self.session.refresh(user)
        return user.orders_amount

    async def get_all_tg_ids(self, *, shop_id: int) -> list[int]:
        stmt = select(ShopUser.tg_id).where(ShopUser.shop_id == shop_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def broadcast_message(
        self,
        *,
        shop_id: int,
        bot: Bot,
        photo_id: str | None,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        delay_sec: float = 0.05,
        limit: int | None = None,
    ) -> None:
        tg_ids = await self.get_all_tg_ids(shop_id=shop_id)
        if limit is not None:
            tg_ids = tg_ids[:limit]

        for tg_id in tg_ids:
            await self.send_safe_message(
                bot=bot,
                user_id=tg_id,
                photo_id=photo_id,
                text=text,
                reply_markup=reply_markup,
            )
            if delay_sec > 0:
                await asyncio.sleep(delay_sec)

    @staticmethod
    async def send_safe_message(
        *,
        bot: Bot,
        user_id: int,
        photo_id: str | None,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        try:
            if photo_id:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
        except TelegramBadRequest as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")
