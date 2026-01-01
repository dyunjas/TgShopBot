# main.py
from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from backend.core.config import settings
from backend.core.logger_config import logger
from backend.database.models import Shop
from backend.database.session import async_session, check_connection, engine, init_db

from backend.middlewares.db import DBSessionMiddleware
from backend.middlewares.user_update import UserUpdateMiddleware
from backend.middlewares.shop_context import ShopContextMiddleware, ShopInfo 

from bot.bot_routers import router as bot_router

from orderdrop_bot import orderdrop_routers
from orderdrop_bot.services.drop_worker import publish_new_orders_loop



def make_bot(token: str) -> Bot:
    return Bot(
        token=token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )


async def load_active_fingerprint() -> Dict[int, Tuple[str, str]]:

    async with async_session() as session:
        res = await session.execute(
            select(Shop).where(Shop.is_active.is_(True)).order_by(Shop.id.asc())
        )
        shops = res.scalars().all()

    fp: Dict[int, Tuple[str, str]] = {}
    for s in shops:
        token = (s.bot_token or "").strip()
        if not token:
            continue
        fp[int(s.id)] = (token, (s.title or "").strip())
    return fp


async def build_bots_and_mapping(fp: Dict[int, Tuple[str, str]]) -> tuple[list[Bot], dict[int, ShopInfo]]:

    bots: list[Bot] = []
    bot_id_to_shop: dict[int, ShopInfo] = {}

    for shop_id, (token, title) in fp.items():
        bot = make_bot(token)
        try:
            me = await bot.get_me()
        except Exception:
            with suppress(Exception):
                await bot.session.close()
            logger.exception(f"[SHOPS] bad token for shop_id={shop_id} (cannot get_me)")
            continue

        bots.append(bot)
        bot_id_to_shop[int(me.id)] = ShopInfo(id=int(shop_id), title=title or None)

    return bots, bot_id_to_shop


async def start_drop_polling(drop_bot: Bot):
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(UserUpdateMiddleware())
    dp.include_router(orderdrop_routers.router)

    with suppress(Exception):
        await drop_bot.delete_webhook(drop_pending_updates=True)

    logger.info("[DROP] polling started")
    await dp.start_polling(drop_bot)


@dataclass
class ShopsRuntime:
    dp: Dispatcher
    bot_id_to_shop: Dict[int, ShopInfo]
    bots: List[Bot]
    polling_task: Optional[asyncio.Task]


async def start_shops_polling(rt: ShopsRuntime, bots: list[Bot], mapping: dict[int, ShopInfo]) -> None:
    rt.bot_id_to_shop.clear()
    rt.bot_id_to_shop.update(mapping)

    rt.bots = bots

    for b in bots:
        with suppress(Exception):
            await b.delete_webhook(drop_pending_updates=True)

    async def _run():
        logger.info(f"[SHOPS] polling started for {len(bots)} bots")
        try:
            await rt.dp.start_polling(*bots)
        finally:
            logger.info("[SHOPS] polling stopped")

    rt.polling_task = asyncio.create_task(_run(), name="shops:polling")


async def stop_shops_polling(rt: ShopsRuntime) -> None:
    try:
        await rt.dp.stop_polling()
    except Exception:
        pass

    if rt.polling_task:
        rt.polling_task.cancel()
        with suppress(Exception):
            await rt.polling_task
        rt.polling_task = None

    for b in rt.bots:
        with suppress(Exception):
            await b.session.close()

    rt.bots = []
    rt.bot_id_to_shop.clear()


async def shops_supervisor_loop(interval: float = 2.0, debounce_sec: float = 2.0):

    bot_id_to_shop: Dict[int, ShopInfo] = {}

    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(ShopContextMiddleware(bot_id_to_shop)) 
    dp.update.middleware(UserUpdateMiddleware())
    dp.include_router(bot_router)

    rt = ShopsRuntime(dp=dp, bot_id_to_shop=bot_id_to_shop, bots=[], polling_task=None)

    last_fp: Dict[int, Tuple[str, str]] = await load_active_fingerprint()

    bots, mapping = await build_bots_and_mapping(last_fp)
    await start_shops_polling(rt, bots, mapping)

    pending_restart_at: float | None = None

    while True:
        await asyncio.sleep(interval)

        try:
            fp_new = await load_active_fingerprint()

            if fp_new != last_fp:
                last_fp = fp_new
                pending_restart_at = asyncio.get_running_loop().time() + debounce_sec
                continue

            if pending_restart_at is not None:
                now = asyncio.get_running_loop().time()
                if now >= pending_restart_at:
                    pending_restart_at = None
                    logger.info("[SHOPS] applying changes (debounced restart)")

                    await stop_shops_polling(rt)

                    bots2, mapping2 = await build_bots_and_mapping(last_fp)
                    await start_shops_polling(rt, bots2, mapping2)

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("[SHOPS] supervisor crashed")


async def main():
    await init_db()
    await check_connection()

    drop_bot = make_bot(settings.DROP_BOT_TOKEN)

    drop_poll_task = asyncio.create_task(start_drop_polling(drop_bot), name="drop:polling")
    drop_worker_task = asyncio.create_task(publish_new_orders_loop(drop_bot, async_session), name="drop:worker")
    shops_task = asyncio.create_task(shops_supervisor_loop(interval=2.0, debounce_sec=2.0), name="shops:supervisor")

    logger.info("✅ Drop bot + shops polling started")

    try:
        await asyncio.gather(drop_poll_task, drop_worker_task, shops_task)
    finally:
        for t in (shops_task, drop_worker_task, drop_poll_task):
            t.cancel()
        for t in (shops_task, drop_worker_task, drop_poll_task):
            with suppress(Exception):
                await t

        with suppress(Exception):
            await drop_bot.session.close()

        with suppress(Exception):
            await engine.dispose()

        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
