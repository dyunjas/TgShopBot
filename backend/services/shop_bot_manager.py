from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from backend.core.logger_config import logger
from backend.middlewares.db import DBSessionMiddleware
from backend.middlewares.shop_context import ShopContextMiddleware, ShopInfo
from backend.middlewares.user_update import UserUpdateMiddleware

from bot.bot_routers import router as bot_router


class ShopBotManager:

    def __init__(self):
        self._lock = asyncio.Lock()

        self._tasks: Dict[int, asyncio.Task] = {}
        self._bots: Dict[int, Bot] = {}
        self._bot_ids: Dict[int, int] = {}

        self._bot_id_to_shop: Dict[int, ShopInfo] = {}

        self._dp = Dispatcher(storage=MemoryStorage())
        self._dp.update.middleware(DBSessionMiddleware())
        self._dp.update.middleware(ShopContextMiddleware(self._bot_id_to_shop))
        self._dp.update.middleware(UserUpdateMiddleware())
        self._dp.include_router(bot_router)

    def _make_bot(self, token: str) -> Bot:
        return Bot(
            token=token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True,
            ),
        )

    async def _poll_one_bot(self, bot: Bot, shop_id: int, title: str):
        try:
            with suppress(Exception):
                await bot.delete_webhook(drop_pending_updates=True)

            logger.info(f"[SHOP:{shop_id}:{title}] polling started")

            await self._dp._polling(bot) 

        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception(f"[SHOP:{shop_id}:{title}] polling crashed")
        finally:
            with suppress(Exception):
                await bot.session.close()
            logger.info(f"[SHOP:{shop_id}:{title}] stopped")

    async def start_shop(self, *, shop_id: int, token: str, title: str):
        async with self._lock:
            t = self._tasks.get(shop_id)
            if t and not t.done():
                return

            await self._stop_nolock(shop_id)

            bot = self._make_bot(token)
            try:
                me = await bot.get_me()
            except Exception:
                with suppress(Exception):
                    await bot.session.close()
                raise

            bot_id = int(me.id)
            self._bot_id_to_shop[bot_id] = ShopInfo(id=shop_id, title=title)

            task = asyncio.create_task(self._poll_one_bot(bot, shop_id, title), name=f"shop:{shop_id}")
            self._bots[shop_id] = bot
            self._bot_ids[shop_id] = bot_id
            self._tasks[shop_id] = task

    async def _stop_nolock(self, shop_id: int):
        task = self._tasks.pop(shop_id, None)
        bot = self._bots.pop(shop_id, None)
        bot_id = self._bot_ids.pop(shop_id, None)

        if task and not task.done():
            task.cancel()
            with suppress(Exception):
                await task  

        if bot:
            with suppress(Exception):
                await bot.session.close()

        if bot_id is not None:
            self._bot_id_to_shop.pop(int(bot_id), None)

        logger.info(f"[SHOP:{shop_id}] stopped")

    async def stop_shop(self, shop_id: int):
        async with self._lock:
            await self._stop_nolock(shop_id)

    async def restart_shop(self, *, shop_id: int, token: str, title: str):
        async with self._lock:
            await self._stop_nolock(shop_id)
            bot = self._make_bot(token)
            try:
                me = await bot.get_me()
            except Exception:
                with suppress(Exception):
                    await bot.session.close()
                raise

            bot_id = int(me.id)
            self._bot_id_to_shop[bot_id] = ShopInfo(id=shop_id, title=title)

            task = asyncio.create_task(self._poll_one_bot(bot, shop_id, title), name=f"shop:{shop_id}")
            self._bots[shop_id] = bot
            self._bot_ids[shop_id] = bot_id
            self._tasks[shop_id] = task

    async def is_running(self, shop_id: int) -> bool:
        async with self._lock:
            t = self._tasks.get(shop_id)
            return bool(t and not t.done())
