from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings


def _default_props() -> DefaultBotProperties:
    return DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    )


async def setup_droporders_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.DROP_BOT_TOKEN,
        default=_default_props(),
    )
    dp = Dispatcher(storage=MemoryStorage())
    return bot, dp


def make_shop_bot(token: str) -> Bot:
    return Bot(
        token=token,
        default=_default_props(),
    )


def make_dispatcher() -> Dispatcher:
    return Dispatcher(storage=MemoryStorage())


async def shutdown_bot(bot: Bot):
    await bot.session.close()