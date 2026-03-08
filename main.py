# main.py
from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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
    drop_token = (settings.DROP_BOT_TOKEN or "").strip()
    for s in shops:
        token = (s.bot_token or "").strip()
        if not token:
            continue
        if drop_token and token == drop_token:
            logger.warning(f"[SHOPS] shop_id={int(s.id)} uses DROP_BOT_TOKEN, skipping from shops polling")
            continue
        fp[int(s.id)] = (token, (s.title or "").strip())
    return fp


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
class ShopPollingEntry:
    shop_id: int
    token: str
    title: str
    bot: Bot
    bot_id: int
    task: asyncio.Task


@dataclass
class ShopsRuntime:
    dp: Dispatcher
    bot_id_to_shop: Dict[int, ShopInfo]
    entries: Dict[int, ShopPollingEntry]


def _make_shop_dispatcher(bot_id_to_shop: Dict[int, ShopInfo]) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(ShopContextMiddleware(bot_id_to_shop))
    dp.update.middleware(UserUpdateMiddleware())
    dp.include_router(bot_router)
    return dp


async def _start_shop_polling(rt: ShopsRuntime, *, shop_id: int, token: str, title: str) -> None:
    bot = make_bot(token)
    try:
        me = await bot.get_me()
    except Exception:
        with suppress(Exception):
            await bot.session.close()
        logger.exception(f"[SHOPS] bad token for shop_id={shop_id} (cannot get_me)")
        return

    bot_id = int(me.id)
    if bot_id in rt.bot_id_to_shop:
        with suppress(Exception):
            await bot.session.close()
        logger.warning(f"[SHOPS] bot id={bot_id} already running, skip shop_id={shop_id}")
        return

    rt.bot_id_to_shop[bot_id] = ShopInfo(id=shop_id, title=title or None)

    with suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=True)

    async def _run():
        logger.info(f"[SHOPS] polling started shop_id={shop_id} bot_id={bot_id} title='{title}'")
        try:
            await rt.dp._polling(bot)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception(f"[SHOPS] polling crashed shop_id={shop_id} bot_id={bot_id}")
        finally:
            logger.info(f"[SHOPS] polling stopped shop_id={shop_id} bot_id={bot_id}")

    task = asyncio.create_task(_run(), name=f"shop:{shop_id}")
    rt.entries[shop_id] = ShopPollingEntry(
        shop_id=shop_id,
        token=token,
        title=title,
        bot=bot,
        bot_id=bot_id,
        task=task,
    )


async def _stop_shop_polling(rt: ShopsRuntime, *, shop_id: int, reason: str) -> None:
    entry = rt.entries.pop(shop_id, None)
    if not entry:
        return

    entry.task.cancel()
    with suppress(Exception):
        await entry.task

    with suppress(Exception):
        await entry.bot.session.close()

    rt.bot_id_to_shop.pop(entry.bot_id, None)
    logger.info(f"[SHOPS] shop stopped shop_id={shop_id} bot_id={entry.bot_id} reason={reason}")


async def _sync_shops_polling(rt: ShopsRuntime, fp: Dict[int, Tuple[str, str]]) -> None:
    desired = {int(shop_id): ((token or "").strip(), (title or "").strip()) for shop_id, (token, title) in fp.items()}
    seen_tokens: set[str] = set()
    filtered: Dict[int, Tuple[str, str]] = {}
    for shop_id, (token, title) in desired.items():
        if not token:
            continue
        if token in seen_tokens:
            logger.warning(f"[SHOPS] duplicate bot token detected for shop_id={shop_id}, skipping")
            continue
        seen_tokens.add(token)
        filtered[shop_id] = (token, title)

    current_ids = set(rt.entries.keys())
    desired_ids = set(filtered.keys())

    for shop_id in sorted(current_ids - desired_ids):
        await _stop_shop_polling(rt, shop_id=shop_id, reason="deactivated_or_deleted")

    for shop_id in sorted(desired_ids):
        token, title = filtered[shop_id]
        entry = rt.entries.get(shop_id)
        if not entry:
            await _start_shop_polling(rt, shop_id=shop_id, token=token, title=title)
            continue

        if entry.token != token or entry.title != title:
            await _stop_shop_polling(rt, shop_id=shop_id, reason="token_or_title_changed")
            await _start_shop_polling(rt, shop_id=shop_id, token=token, title=title)


async def _stop_all_shops_polling(rt: ShopsRuntime) -> None:
    for shop_id in list(rt.entries.keys()):
        await _stop_shop_polling(rt, shop_id=shop_id, reason="shutdown")
    rt.bot_id_to_shop.clear()


async def shops_supervisor_loop(interval: float = 2.0, debounce_sec: float = 2.0):
    bot_id_to_shop: Dict[int, ShopInfo] = {}
    rt = ShopsRuntime(
        dp=_make_shop_dispatcher(bot_id_to_shop),
        bot_id_to_shop=bot_id_to_shop,
        entries={},
    )

    last_fp: Dict[int, Tuple[str, str]] = await load_active_fingerprint()
    await _sync_shops_polling(rt, last_fp)

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
                    logger.info("[SHOPS] applying changes (debounced incremental sync)")
                    await _sync_shops_polling(rt, last_fp)

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("[SHOPS] supervisor crashed")

    await _stop_all_shops_polling(rt)


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
