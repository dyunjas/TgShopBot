from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    CallbackQuery
)

from typing import (
    Callable,
    Dict,
    Any,
    Awaitable
)

from ..database.session import async_session

from ..repositories.user_repository import ShopUserRepository
from ..repositories.order_repository import ShopOrderRepository
from ..repositories.transaction_repository import ShopTransactionRepository
from ..repositories.shop_repository import ShopRepository
from ..repositories.promocode_repository import ShopPromocodeRepository
from ..repositories.admin_repository import AdminUserRepository

import logging

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            data["user_repo"] = ShopUserRepository(session)
            data["order_repo"] = ShopOrderRepository(session)
            data["transaction_repo"] = ShopTransactionRepository(session)
            data["shop_repo"] = ShopRepository(session)
            data["promocode_repo"] = ShopPromocodeRepository(session)
            data["admin_repo"] = AdminUserRepository(session)

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logging.error(f"Database error: {e}")
            finally:
                await session.close()