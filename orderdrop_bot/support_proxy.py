from __future__ import annotations

import io
from html import escape

from aiogram import Bot
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from backend.core.config import settings
from backend.core.logger_config import logger


def make_drop_bot() -> Bot:
    return Bot(
        token=settings.DROP_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )


async def _download_as_inputfile(source_bot: Bot, file_id: str, filename: str) -> BufferedInputFile:
    tg_file = await source_bot.get_file(file_id)
    buf = io.BytesIO()
    await source_bot.download_file(tg_file.file_path, destination=buf)
    return BufferedInputFile(buf.getvalue(), filename=filename)


async def relay_user_message_to_topic(
    *,
    shop_bot: Bot,
    drop_bot: Bot,
    message: Message,
    group_chat_id: int,
    topic_id: int,
    shop_id: int,
    order_id: str,
) -> None:
    user_id = message.from_user.id if message.from_user else 0
    username = f"@{message.from_user.username}" if (message.from_user and message.from_user.username) else "-"
    user_header = (
        f"👤 Пользователь: <code>{user_id}</code> ({escape(username)})\n"
        f"🧾 Заказ: <code>{escape(order_id)}</code>\n\n"
    )

    try:
        if message.text:
            await drop_bot.send_message(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                text=user_header + escape(message.text or ""),
            )
            return

        if message.photo:
            best = message.photo[-1]
            caption = ((message.caption or "").strip() or "📷 Фото")
            inp = await _download_as_inputfile(shop_bot, best.file_id, filename="photo.jpg")
            await drop_bot.send_photo(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                photo=inp,
                caption=(user_header + escape(caption))[:1024],
            )
            return

        if message.document:
            doc = message.document
            caption = ((message.caption or "").strip() or f"📎 {doc.file_name or 'Документ'}")
            inp = await _download_as_inputfile(shop_bot, doc.file_id, filename=doc.file_name or "file")
            await drop_bot.send_document(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                document=inp,
                caption=(user_header + escape(caption))[:1024],
            )
            return

        if message.video:
            vid = message.video
            caption = ((message.caption or "").strip() or "🎥 Видео")
            inp = await _download_as_inputfile(shop_bot, vid.file_id, filename="video.mp4")
            await drop_bot.send_video(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                video=inp,
                caption=(user_header + escape(caption))[:1024],
            )
            return

        if message.voice:
            v = message.voice
            caption = ((message.caption or "").strip() or "🎙 Голос")
            inp = await _download_as_inputfile(shop_bot, v.file_id, filename="voice.ogg")
            await drop_bot.send_voice(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                voice=inp,
                caption=(user_header + escape(caption))[:1024],
            )
            return

        if message.audio:
            a = message.audio
            caption = ((message.caption or "").strip() or "🎵 Аудио")
            inp = await _download_as_inputfile(shop_bot, a.file_id, filename=a.file_name or "audio.mp3")
            await drop_bot.send_audio(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                audio=inp,
                caption=(user_header + escape(caption))[:1024],
            )
            return

        if message.sticker:
            s = message.sticker
            inp = await _download_as_inputfile(shop_bot, s.file_id, filename="sticker.webp")
            await drop_bot.send_sticker(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                sticker=inp,
            )
            await drop_bot.send_message(
                chat_id=group_chat_id,
                message_thread_id=topic_id,
                text=user_header + "🧩 Стикер",
            )
            return

        await drop_bot.send_message(
            chat_id=group_chat_id,
            message_thread_id=topic_id,
            text=user_header + "⚠️ Неподдерживаемый тип сообщения",
        )

    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.exception(
            f"relay_user_message_to_topic failed: {e} "
            f"(group_chat_id={group_chat_id}, topic_id={topic_id}, shop_id={shop_id}, order_id={order_id})"
        )
        raise
