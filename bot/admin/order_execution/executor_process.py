from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from backend.core.loader import settings, bot
from backend.core.logger_config import logger

from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.admin_repository import AdminUserRepository
from backend.repositories.user_repository import ShopUserRepository

from .keyboards import take_order_kb, order_in_work_kb, rate_kb, user_msg_kb

router = Router()

REWARD_RUB = getattr(settings, "OPERATOR_REWARD_RUB", 50)


@router.callback_query(F.data.startswith("order_take:"))
async def order_take_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    admin_repo: AdminUserRepository,
):
    order_id = callback.data.split(":")[1]
    username = callback.from_user.username

    admin = await admin_repo.ensure_admin(callback.from_user.id, username)

    order = await order_repo.take_order(
        order_id,
        executor_admin_id=admin.id,
        executor_name=admin.username,
    )
    if not order:
        return await callback.answer("Заказ уже взят или не найден", show_alert=True)

    await callback.message.edit_reply_markup(reply_markup=order_in_work_kb(order_id))

    await bot.send_message(
        chat_id=order.user.tg_id,
        text=(
            "<b>Заказ принят</b>\n\n"
            f"Заказ <b>{order_id}</b> был принят сотрудником <b>{admin.username}</b>\n\n"
            f"Товар: {order.title}\n\n"
            "После выполнения заказа, вы получите уведомление. Чтобы отправить сообщение сотруднику - используйте кнопку ниже."
        ),
        parse_mode="HTML",
        reply_markup=user_msg_kb()
    )

    await callback.answer("Вы взяли заказ ✅")

@router.callback_query(F.data.startswith("order_dialog:"))
async def order_dialog_clb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("💬 Пишите в этот топик — бот отправит сообщение покупателю.")


@router.message(F.chat.id == settings.ORDERS_GROUP_ID)
async def forward_executor_to_user(
    message: Message,
    order_repo: ShopOrderRepository,
):
    if not message.message_thread_id or not message.from_user:
        return

    order = await order_repo.get_by_topic_id(message.message_thread_id)
    if not order or not order.executor_admin_id:
        return

    if order.admin_card_msg_id == message.message_id:
        return

    executor_tg_id = await order_repo.get_executor_tg_id(order.order_id)
    if executor_tg_id != message.from_user.id:
        return

    await bot.copy_message(
        chat_id=order.user.tg_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )


@router.callback_query(F.data.startswith("order_done:"))
async def order_done_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    admin_repo: AdminUserRepository,
):
    order_id = callback.data.split(":")[1]
    order = await order_repo.get_order_by_order_id(order_id)

    if not order or not order.executor_admin_id:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может завершить", show_alert=True)

    await order_repo.set_status(order_id, "done")
    await admin_repo.increase_balance(callback.from_user.id, REWARD_RUB)

    await bot.send_message(
        chat_id=order.user.tg_id,
        text=(
            f"<b>Заказ выполнен</b>\n\n"
            f"Заказ <b>{order_id} - {order.title}</b> был выполнен.\n\n"
            "Оставьте отзыв по кнопке ниже❤️"
        ),
        parse_mode="HTML",
        reply_markup=rate_kb(order_id),
    )

    await _delete_topic_safe(order.group_chat_id, order.topic_id)
    await callback.answer("Готово ✅")


@router.callback_query(F.data.startswith("order_refund:"))
async def order_refund_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    user_repo: ShopUserRepository,
):
    order_id = callback.data.split(":")[1]
    order = await order_repo.get_order_by_order_id(order_id)

    if not order:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может вернуть", show_alert=True)

    if order.status == "refunded":
        return await callback.answer("Уже возвращён", show_alert=True)

    await user_repo.increase_balance(order.user.tg_id, order.price)
    await order_repo.set_status(order_id, "refunded")

    await bot.send_message(
        chat_id=order.user.tg_id,
        text=f"💸 По заказу <code>{order_id}</code> выполнен возврат <b>{order.price}</b> RUB.",
        parse_mode="HTML",
    )

    await _delete_topic_safe(order.group_chat_id, order.topic_id)
    await callback.answer("Возврат выполнен", show_alert=True)


async def _delete_topic_safe(group_chat_id: int | None, topic_id: int | None):
    if not group_chat_id or not topic_id:
        return
    try:
        await bot.delete_forum_topic(chat_id=group_chat_id, message_thread_id=topic_id)
    except Exception:
        try:
            await bot.close_forum_topic(chat_id=group_chat_id, message_thread_id=topic_id)
        except Exception:
            pass


@router.message(lambda m: m.text == "/balance")
async def admin_balance_cmd(
    message: Message,
    admin_repo: AdminUserRepository
):
    if message.from_user.id not in settings.ADMIN_IDS:
        return

    admin = await admin_repo.get_by_tg_id(message.from_user.id)
    if not admin:
        return

    await message.answer(
        f"💰 <b>Ваш баланс:</b> <code>{admin.balance}</code> RUB\nНапишите администратору для вывода.",
        parse_mode="HTML"
    )
