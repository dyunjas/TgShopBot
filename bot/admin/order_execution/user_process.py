from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from backend.core.loader import settings, bot
from backend.core.logger_config import logger
from backend.repositories.order_repository import ShopOrderRepository
from backend.states import ReviewSG, SupportChatSG

router = Router()


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
    order_repo: ShopOrderRepository,
):
    order = await order_repo.get_last_open_order_for_user(message.from_user.id)
    if not order:
        await message.answer("У вас нет активного заказа для поддержки.")
        return

    try:
        await bot.copy_message(
            chat_id=order.group_chat_id,
            message_thread_id=order.topic_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"Failed to forward user message to topic: {e}")
        await message.answer("Не удалось отправить сообщение в поддержку.")


@router.callback_query(F.data.startswith("rate:"))
async def rate_choose_clb(callback: CallbackQuery, state: FSMContext):
    _, order_id, stars = callback.data.split(":")
    await state.update_data(order_id=order_id, stars=int(stars))

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("✍️ Напишите комментарий к отзыву (можно коротко).")
    await state.set_state(ReviewSG.waiting_comment)
    await callback.answer()


@router.message(ReviewSG.waiting_comment)
async def review_comment_msg(
    message: Message,
    state: FSMContext,
    order_repo: ShopOrderRepository,
):
    data = await state.get_data()
    order_id = data["order_id"]
    stars = int(data["stars"])
    comment = (message.text or "").strip()

    order = await order_repo.get_order_by_order_id(order_id)
    if not order:
        await state.clear()
        return await message.answer("Заказ не найден.")

    await order_repo.set_review(order_id, rating=stars, review_text=comment)

    display_name = (message.from_user.full_name or "").strip() or "Пользователь"

    item_title = (getattr(order, "title", None) or "").strip() or "—"

    review_text = (
        f"⭐ Оценка: <b>{stars}/5</b>\n"
        f"👤 Пользователь: <b>{display_name}</b>\n"
        f"🛒 Товар: <b>{item_title}</b>\n\n"
        f"📝 Отзыв: {comment if comment else '—'}\n\n"
    )

    await bot.send_message(
        chat_id=settings.REVIEWS_CHANNEL_ID,
        text=review_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await message.answer("Спасибо за отзыв! ❤️")
    await state.clear()
