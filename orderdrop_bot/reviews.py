from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from backend.core.logger_config import logger
from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.shop_repository import ShopRepository
from backend.states import ReviewSG

router = Router()


@router.callback_query(F.data.startswith("rate:"))
async def rate_choose_clb(callback: CallbackQuery, state: FSMContext):
    try:
        _, order_id, stars = callback.data.split(":")
        stars_i = int(stars)
    except Exception:
        return await callback.answer("Кнопка устарела", show_alert=True)

    await state.update_data(order_id=order_id, stars=stars_i)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("✍️ Напишите комментарий к отзыву")
    await state.set_state(ReviewSG.waiting_comment)
    await callback.answer()


@router.message(ReviewSG.waiting_comment, F.chat.type == "private")
async def review_comment_msg(
    message: Message,
    state: FSMContext,
    shop_id: int,
    order_repo: ShopOrderRepository,
    shop_repo: ShopRepository,
):
    data = await state.get_data()
    order_id = data.get("order_id")
    stars = int(data.get("stars") or 0)
    comment = (message.text or "").strip()

    if not order_id or not stars:
        await state.clear()
        return await message.answer("Сессия отзыва истекла. Попробуйте ещё раз.")

    order = await order_repo.get_order_by_order_id(shop_id=shop_id, order_id=order_id)
    if not order:
        await state.clear()
        return await message.answer("Заказ не найден.")

    try:
        await order_repo.set_review(shop_id=shop_id, order_id=order_id, rating=stars, review_text=comment)
    except Exception as e:
        logger.exception(f"Failed set_review: {e} (shop_id={shop_id}, order_id={order_id})")
        await state.clear()
        return await message.answer("Не удалось сохранить отзыв. Попробуйте позже.")

    display_name = (message.from_user.full_name or "").strip() if message.from_user else ""
    display_name = display_name or "Пользователь"
    item_title = (getattr(order, "title", None) or "").strip() or "—"


    review_text = (
        f"⭐ Оценка: <b>{stars}/5</b>\n"
        f"👤 Пользователь: <b>{display_name}</b>\n"
        f"🛒 Товар: <b>{item_title}</b>\n\n"
        f"📝 Отзыв: {comment}\n"
    )

    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
    channel_id = int(getattr(shop, "reviews_channel_id", 0) or 0)

    if channel_id != 0:
        try:
            await message.bot.send_message(
                chat_id=channel_id,
                text=review_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.exception(f"Failed send review to channel: {e} (shop_id={shop_id}, channel_id={channel_id})")

    await message.answer("Спасибо за отзыв! ❤️")
    await state.clear()
