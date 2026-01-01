# backend/middlewares/db_session.py
from __future__ import annotations

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ..database.session import async_session

from ..repositories.user_repository import ShopUserRepository
from ..repositories.order_repository import ShopOrderRepository
from ..repositories.transaction_repository import ShopTransactionRepository
from ..repositories.shop_repository import ShopRepository
from ..repositories.promocode_repository import ShopPromocodeRepository
from ..repositories.admin_repository import AdminUserRepository
from ..repositories.shop_page_repository import ShopPageRepository
from ..repositories.payment_config_repo import PaymentConfigRepository


logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session

            data["user_repo"] = ShopUserRepository(session)
            data["order_repo"] = ShopOrderRepository(session)
            data["transaction_repo"] = ShopTransactionRepository(session)
            data["shop_repo"] = ShopRepository(session)
            data["promocode_repo"] = ShopPromocodeRepository(session)
            data["admin_repo"] = AdminUserRepository(session)

            data["page_repo"] = ShopPageRepository(session)
            data["payment_cfg_repo"] = PaymentConfigRepository(session)

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                logger.exception("Database error")
                raise
