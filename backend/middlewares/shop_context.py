from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


@dataclass(frozen=True)
class ShopInfo:
    id: int
    title: str | None = None


class ShopContextMiddleware(BaseMiddleware):

    def __init__(self, bot_id_to_shop: Mapping[int, ShopInfo]):
        super().__init__()
        self.bot_id_to_shop = bot_id_to_shop

    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data.get("bot")
        bot_id = getattr(bot, "id", None)

        if bot_id is not None:
            info = self.bot_id_to_shop.get(int(bot_id))
            if info:
                data["shop_id"] = info.id
                if info.title:
                    data["shop_title"] = info.title

        return await handler(event, data)
