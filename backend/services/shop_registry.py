from __future__ import annotations

from typing import Dict

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from backend.middlewares.shop_context import ShopInfo


class ShopRegistry:
    def __init__(self):
        self.bots: Dict[int, Bot] = {}
        self.bot_id_to_shop: Dict[int, ShopInfo] = {}

    async def sync(self, shops):
        for bot in self.bots.values():
            await bot.session.close()

        self.bots.clear()
        self.bot_id_to_shop.clear()

        for s in shops:
            bot = Bot(
                s.bot_token,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML,
                    link_preview_is_disabled=True,
                ),
            )
            me = await bot.get_me()

            self.bots[s.id] = bot
            self.bot_id_to_shop[int(me.id)] = ShopInfo(id=s.id, title=s.title)
