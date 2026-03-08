from __future__ import annotations

import io
from html import escape

from aiogram import Bot
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.core.logger_config import logger
from backend.repositories.shop_repository import ShopRepository


def _make_shop_bot(token: str) -> Bot:
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )


async def _download_as_inputfile(source_bot: Bot, file_id: str, filename: str) -> BufferedInputFile:
    tg_file = await source_bot.get_file(file_id)
    buf = io.BytesIO()
    await source_bot.download_file(tg_file.file_path, destination=buf)
    return BufferedInputFile(buf.getvalue(), filename=filename)


def _reply_to_support_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Отправить сообщение", callback_data="support_chat:start")
    return kb.as_markup()


def _make_header(*, operator_name: str, order_id: str) -> str:
    return (
        f"Сотрудник <b>{escape(operator_name)}</b> <b>{escape(order_id)}</b> 🔥🍪\n\n"
    )


async def relay_admin_message_to_user(
    *,
    drop_bot: Bot, 
    shop_repo: ShopRepository,
    shop_id: int,
    user_tg_id: int,
    order_id: str,  
    message: Message,
    operator_name: str | None = None,
) -> None:
    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
    token = getattr(shop, "bot_token", None) if shop else None
    if not token:
        logger.warning(f"relay_admin_message_to_user: shop bot_token missing (shop_id={shop_id})")
        return

    shop_bot = _make_shop_bot(token)

    operator = (operator_name or "").strip() or "Сотрудник"
    header = _make_header(operator_name=operator, order_id=order_id)
    reply_kb = _reply_to_support_kb()

    try:
        if message.text:
            text = header + escape(message.text or "")
            try:
                await shop_bot.send_message(chat_id=user_tg_id, text=text, reply_markup=reply_kb)
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send text to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.photo:
            best = message.photo[-1]
            inp = await _download_as_inputfile(drop_bot, best.file_id, "photo.jpg")
            cap = (message.caption or "").strip()
            caption = (header + escape(cap))[:1024] if cap else (header + "📷 Фото")[:1024]
            try:
                await shop_bot.send_photo(
                    chat_id=user_tg_id,
                    photo=inp,
                    caption=caption,
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send photo to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.document:
            doc = message.document
            inp = await _download_as_inputfile(drop_bot, doc.file_id, doc.file_name or "file")
            cap = (message.caption or "").strip()
            fallback = f"📎 {doc.file_name or 'Документ'}"
            caption = (header + escape(cap))[:1024] if cap else (header + escape(fallback))[:1024]
            try:
                await shop_bot.send_document(
                    chat_id=user_tg_id,
                    document=inp,
                    caption=caption,
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send document to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.video:
            vid = message.video
            inp = await _download_as_inputfile(drop_bot, vid.file_id, "video.mp4")
            cap = (message.caption or "").strip()
            caption = (header + escape(cap))[:1024] if cap else (header + "🎥 Видео")[:1024]
            try:
                await shop_bot.send_video(
                    chat_id=user_tg_id,
                    video=inp,
                    caption=caption,
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send video to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.voice:
            v = message.voice
            inp = await _download_as_inputfile(drop_bot, v.file_id, "voice.ogg")
            cap = (message.caption or "").strip()
            caption = (header + escape(cap))[:1024] if cap else (header + "🎙 Голос")[:1024]
            try:
                await shop_bot.send_voice(
                    chat_id=user_tg_id,
                    voice=inp,
                    caption=caption,
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send voice to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.audio:
            a = message.audio
            inp = await _download_as_inputfile(drop_bot, a.file_id, a.file_name or "audio.mp3")
            cap = (message.caption or "").strip()
            caption = (header + escape(cap))[:1024] if cap else (header + "🎵 Аудио")[:1024]
            try:
                await shop_bot.send_audio(
                    chat_id=user_tg_id,
                    audio=inp,
                    caption=caption,
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send audio to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        if message.sticker:
            s = message.sticker
            inp = await _download_as_inputfile(drop_bot, s.file_id, "sticker.webp")
            try:
                await shop_bot.send_sticker(chat_id=user_tg_id, sticker=inp)
                await shop_bot.send_message(
                    chat_id=user_tg_id,
                    text=header + "🧩 Стикер",
                    reply_markup=reply_kb,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.exception(f"Failed send sticker to user={user_tg_id} shop_id={shop_id}: {e}")
            return

        try:
            await shop_bot.send_message(
                chat_id=user_tg_id,
                text=header + "⚠️ Сообщение поддержки: тип не поддерживается.",
                reply_markup=reply_kb,
            )
        except Exception as e:
            logger.exception(f"Failed send fallback to user={user_tg_id} shop_id={shop_id}: {e}")

    finally:
        await shop_bot.session.close()
