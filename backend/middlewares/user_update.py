# backend/middlewares/user_update.py
from __future__ import annotations

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.user_repository import ShopUserRepository


class UserUpdateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: User | None = data.get("event_from_user")
        session: AsyncSession | None = data.get("session")
        shop_id: int | None = data.get("shop_id")

        if event_user is None or session is None or shop_id is None:
            return await handler(event, data)

        user_repo: ShopUserRepository = data.get("user_repo") or ShopUserRepository(session)
        await self._check_or_create_user(shop_id=shop_id, tg_user=event_user, user_repo=user_repo)

        return await handler(event, data)

    async def _check_or_create_user(
        self,
        *,
        shop_id: int,
        tg_user: User,
        user_repo: ShopUserRepository,
    ) -> None:
        user = await user_repo.get_user(shop_id=shop_id, tg_id=tg_user.id)

        username = tg_user.username 
        full_name = (tg_user.full_name or "").strip()

        if user:
            if getattr(user, "username", None) != username:
                await user_repo.update_username(
                    shop_id=shop_id,
                    tg_id=tg_user.id,
                    new_username=username,
                )
        else:
            await user_repo.create_user(
                shop_id=shop_id,
                tg_id=tg_user.id,
                username=username
            )
