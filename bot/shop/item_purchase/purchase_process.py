from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from backend.core.logger_config import logger
from backend.repositories.order_repository import ShopOrderRepository
from backend.states import SupportChatSG

from orderdrop_bot.support_proxy import make_drop_bot, relay_user_message_to_topic

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

router = Router()


def support_chat_kb_user() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Отправить сообщение", callback_data="support_chat:start")
    return kb.as_markup()


@router.callback_query(F.data == "support_chat:start")
async def support_chat_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportChatSG.active)
    await callback.answer()
    await callback.message.answer(
        "💬 Напишите сообщение — оно будет передано сотруднику.\n"
        "Чтобы выйти из диалога, отправьте /cancel"
    )


@router.message(F.chat.type == "private", F.text == "/cancel")
async def support_chat_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог закрыт ✅")


@router.message(SupportChatSG.active, F.chat.type == "private", ~F.text.regexp(r"^/"))
async def forward_user_to_topic(
    message: Message,
    shop_id: int,
    order_repo: ShopOrderRepository,
):
    if not message.from_user:
        return

    tg_id = message.from_user.id

    order = await order_repo.get_last_open_order_for_user(shop_id=shop_id, tg_id=tg_id)
    if not order:
        await message.answer("У вас нет активного заказа для поддержки.")
        logger.warning(f"SupportChat: no open order (shop_id={shop_id}, tg_id={tg_id})")
        return

    if not getattr(order, "drop_group_chat_id", None) or not getattr(order, "drop_topic_id", None):
        await message.answer("Поддержка ещё не подключена к вашему заказу. Попробуйте позже.")
        logger.warning(
            "SupportChat: missing drop ids "
            f"(shop_id={shop_id}, tg_id={tg_id}, order_id={getattr(order,'order_id',None)}, "
            f"drop_group={getattr(order,'drop_group_chat_id',None)}, drop_topic={getattr(order,'drop_topic_id',None)})"
        )
        return

    drop_bot = make_drop_bot()
    try:
        await relay_user_message_to_topic(
            shop_bot=message.bot,   # текущий SHOP-бот
            drop_bot=drop_bot,      # DropOrders bot
            message=message,
            group_chat_id=order.drop_group_chat_id,
            topic_id=order.drop_topic_id,
            shop_id=shop_id,
            order_id=order.order_id,
        )

        try:
            await message.delete()
        except TelegramBadRequest as e:
            logger.warning(f"SupportChat: cannot delete user message: {e}")

        header = f"Вы <b>{order.order_id}</b> 🔥🍪\n\n"

        if message.text:
            preview = message.text

        elif message.caption:
            preview = message.caption

        elif message.photo:
            preview = "📷 Фото"

        elif message.video:
            preview = "🎥 Видео"

        elif message.document:
            preview = f"📎 {message.document.file_name or 'Документ'}"

        elif message.voice:
            preview = "🎙 Голосовое сообщение"

        elif message.audio:
            preview = f"🎵 {message.audio.file_name or 'Аудио'}"

        elif message.sticker:
            preview = "🧩 Стикер"

        else:
            preview = "✅ Сообщение отправлено"

        await message.answer(
            text=header + preview,
            reply_markup=support_chat_kb_user(),
        )

    except Exception as e:
        logger.exception(f"Failed to relay user message to topic: {e}")
        await message.answer("Не удалось отправить сообщение в поддержку.")
    finally:
        await drop_bot.session.close()

