from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.shop_repository import ShopRepository
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.order_repository import ShopOrderRepository

from backend.images.images_url import CONFIRM_PURCHASE_URL, SUCCESS_PURCHASE_MENU

from .keyboards import (
    build_item_kb,
    insufficient_funds_kb,
    order_support_kb,
    build_confirm_purchase_kb,
    take_order_kb
)

from backend.core.loader import settings, bot
from backend.core.logger_config import logger

router = Router()


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase_clb(
    callback: CallbackQuery,
    shop_repo: ShopRepository,
    user_repo: ShopUserRepository,
    order_repo: ShopOrderRepository
):
    tg_id = callback.from_user.id
    item_id = int(callback.data.split(":")[1])

    item = await shop_repo.get_item_by_id(item_id)
    user = await user_repo.get_user(tg_id)

    if not item or not user:
        await callback.answer("Ошибка покупки", show_alert=True)
        logger.error(f"Purchase error: item or user not found (tg_id={tg_id}, item_id={item_id})")
        return

    if user.balance < item.price:
        await callback.message.edit_caption(
            caption="Недостаточно средств, пополните баланс",
            reply_markup=insufficient_funds_kb()
        )
        logger.info(
            f"Purchase failed due to insufficient funds (tg_id={tg_id}, item_id={item_id}, "
            f"balance={user.balance}, price={item.price})"
        )
        return

    await user_repo.decrease_balance(tg_id, item.price)
    await user_repo.increase_orders_amount(tg_id, 1)

    order = await order_repo.create_order(
        title=item.title,
        price=item.price,
        tg_id=user.tg_id
    )

    try:
        topic = await bot.create_forum_topic(
            chat_id=settings.ORDERS_GROUP_ID,
            name=f"Заказ {order.order_id} | {item.title}"
        )
        topic_id = topic.message_thread_id

        admin_first_text = (
            "<b>Оформление заказа</b>\n\n"
            f"<b>Товар:</b> {item.title}\n"
            f"<b>Цена:</b> {item.price} RUB\n"
            f"<b>Номер заказа:</b> <code>{order.order_id}</code>\n\n"
        )

        first_msg = await bot.send_message(
            chat_id=settings.ORDERS_GROUP_ID,
            message_thread_id=topic_id,
            text=admin_first_text,
            parse_mode="HTML",
            reply_markup=take_order_kb(order.order_id),
        )

        if hasattr(order_repo, "set_admin_topic"):
            await order_repo.set_admin_topic(
                order_id=order.order_id,
                group_chat_id=settings.ORDERS_GROUP_ID,
                topic_id=topic_id,
                admin_card_msg_id=first_msg.message_id
            )

    except Exception as e:
        logger.error(f"Failed to create forum topic for order {order.order_id}: {e}")

    user_text = (
        "✅ <b>Заказ был успешно оформлен!</b>\n\n"
        "<i>Он будет принят сотрудником в порядке очереди."
        "Обычно это занимает не более часа, но зависит от текущей очереди заказов.</i>\n\n"
        f"<b>Товар:</b> {item.title}\n"
        f"<b>Номер заказа:</b> <code>{order.order_id}</code>"
    )

    content = InputMediaPhoto(
        media=SUCCESS_PURCHASE_MENU,
        caption=user_text,
        parse_mode="HTML"
    )

    await callback.message.edit_media(
        media=content
    )

    logger.info(f"Purchase successful (tg_id={tg_id}, item_id={item_id}, order_id={order.order_id})")
    await callback.answer()
