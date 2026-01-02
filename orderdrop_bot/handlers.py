from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from backend.core.config import settings
from backend.core.logger_config import logger
from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.admin_repository import AdminUserRepository
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.shop_repository import ShopRepository

from .keyboards import order_in_work_kb, confirm_done_kb, confirm_refund_kb, rate_kb
from .support_admin_proxy import relay_admin_message_to_user

from bot.shop.item_purchase.keyboards import support_chat_kb

router = Router()
REWARD_RUB = getattr(settings, "OPERATOR_REWARD_RUB", 50)


def _parse_two_ids(callback_data: str, prefix: str) -> tuple[int, str] | None:
    parts = callback_data.split(":")
    if len(parts) != 3 or parts[0] != prefix:
        return None
    try:
        return int(parts[1]), parts[2]
    except Exception:
        return None


async def _get_user_tg_id_safe(
    order_repo: ShopOrderRepository, shop_id: int, order_id: str, order_obj=None
) -> int | None:
    if order_obj is not None:
        try:
            if getattr(order_obj, "user", None) is not None and getattr(order_obj.user, "tg_id", None):
                return int(order_obj.user.tg_id)
        except Exception:
            pass
    return await order_repo.get_user_tg_id_by_order(shop_id=shop_id, order_id=order_id)


@router.callback_query(F.data.startswith("order_take:"))
async def order_take_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    admin_repo: AdminUserRepository,
    shop_repo: ShopRepository,
):
    parsed = _parse_two_ids(callback.data, "order_take")
    if not parsed:
        return await callback.answer("Кнопка устарела. Обновите карточку заказа.", show_alert=True)

    shop_id, order_id = parsed

    admin = await admin_repo.ensure_admin(callback.from_user.id)
    if not admin:
        return await callback.answer("Сотрудник не найден", show_alert=True)

    order = await order_repo.take_order(
        shop_id=shop_id,
        order_id=order_id,
        executor_admin_id=admin.id,
        executor_name=admin.username or "Сотрудник",
    )
    if not order:
        return await callback.answer("Заказ уже взят или не найден", show_alert=True)

    try:
        await callback.message.edit_reply_markup(reply_markup=order_in_work_kb(shop_id, order_id))
    except Exception:
        pass

    user_tg_id = await _get_user_tg_id_safe(order_repo, shop_id, order_id, order_obj=order)
    if not user_tg_id:
        logger.warning(f"order_take: cannot resolve user_tg_id (shop_id={shop_id}, order_id={order_id})")
    else:
        shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
        if shop and getattr(shop, "bot_token", None):
            from aiogram import Bot
            from aiogram.enums import ParseMode
            from aiogram.client.default import DefaultBotProperties

            shop_bot = Bot(
                token=shop.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
            )
            try:
                await shop_bot.send_message(
                    chat_id=user_tg_id,
                    text=(
                        "<b>Заказ принят</b>\n\n"
                        f"Заказ <b>{order_id}</b> принят сотрудником <b>{admin.username or 'Сотрудник'}</b>\n\n"
                        f"Товар: {order.title}\n\n"
                        "💬 Чтобы написать сотруднику - нажмите на кнопку ниже. "
                        "После выполнения заказа, вы получите уведомление."
                    ),
                    reply_markup=support_chat_kb(),
                )
            except Exception as e:
                logger.exception(
                    f"Failed to notify user about order_take: {e} "
                    f"(shop_id={shop_id}, order_id={order_id}, user_tg_id={user_tg_id})"
                )
            finally:
                await shop_bot.session.close()

    await callback.answer("Вы взяли заказ ✅")


@router.message()
async def forward_executor_to_user(
    message: Message,
    order_repo: ShopOrderRepository,
    shop_repo: ShopRepository,
):
    logger.info(
        f"DROP MSG: chat_id={message.chat.id} thread={message.message_thread_id} "
        f"from={message.from_user.id if message.from_user else None} msg_id={message.message_id}"
    )

    if int(message.chat.id) != int(settings.ORDERS_GROUP_ID):
        return
    if not message.message_thread_id or not message.from_user:
        return

    order = await order_repo.get_by_drop_topic_id(message.message_thread_id)
    if not order:
        logger.warning(f"No order for topic_id={message.message_thread_id}")
        return

    if not order.executor_admin_id:
        return

    if order.admin_card_msg_id == message.message_id:
        return

    executor_tg_id = await order_repo.get_executor_tg_id(shop_id=order.shop_id, order_id=order.order_id)
    if executor_tg_id != message.from_user.id:
        return

    user_tg_id = await _get_user_tg_id_safe(order_repo, order.shop_id, order.order_id, order_obj=order)
    if not user_tg_id:
        logger.warning(
            f"forward_executor_to_user: cannot resolve user_tg_id (shop_id={order.shop_id}, order_id={order.order_id})"
        )
        return

    await relay_admin_message_to_user(
        drop_bot=message.bot,
        shop_repo=shop_repo,
        shop_id=order.shop_id,
        user_tg_id=user_tg_id,
        message=message,
        order_id=order.order_id,  
    )


@router.callback_query(F.data.startswith("order_done:"))
async def order_done_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    parsed = _parse_two_ids(callback.data, "order_done")
    if not parsed:
        return await callback.answer("Кнопка устарела. Обновите карточку заказа.", show_alert=True)
    shop_id, order_id = parsed

    order = await order_repo.get_order_by_order_id(shop_id=shop_id, order_id=order_id)
    if not order or not order.executor_admin_id:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(shop_id=shop_id, order_id=order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может завершить", show_alert=True)

    try:
        await callback.message.edit_reply_markup(reply_markup=confirm_done_kb(shop_id, order_id))
    except Exception:
        pass

    await callback.answer("Подтвердите выполнение ✅")


@router.callback_query(F.data.startswith("order_done_confirm:"))
async def order_done_confirm_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    admin_repo: AdminUserRepository,
    shop_repo: ShopRepository,
):
    parsed = _parse_two_ids(callback.data, "order_done_confirm")
    if not parsed:
        return await callback.answer("Кнопка устарела. Обновите карточку заказа.", show_alert=True)
    shop_id, order_id = parsed

    order = await order_repo.get_order_by_order_id(shop_id=shop_id, order_id=order_id)
    if not order:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(shop_id=shop_id, order_id=order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может завершить", show_alert=True)

    await order_repo.set_status(shop_id=shop_id, order_id=order_id, status="done")
    await admin_repo.increase_balance(callback.from_user.id, REWARD_RUB)

    user_tg_id = await _get_user_tg_id_safe(order_repo, shop_id, order_id, order_obj=order)
    if user_tg_id:
        shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
        if shop and getattr(shop, "bot_token", None):
            from aiogram import Bot
            from aiogram.enums import ParseMode
            from aiogram.client.default import DefaultBotProperties

            shop_bot = Bot(
                token=shop.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
            )
            try:
                await shop_bot.send_message(
                    chat_id=user_tg_id,
                    text=(
                        "<b>Заказ выполнен</b>\n\n"
                        f"Заказ <b>{order_id}</b> - <b>{order.title}</b> был выполнен.\n\n"
                        "Оставьте отзыв по кнопке ниже ❤️"
                    ),
                    reply_markup=rate_kb(shop_id, order_id)
                )
            except Exception as e:
                logger.exception(
                    f"Failed to notify user about order_done: {e} "
                    f"(shop_id={shop_id}, order_id={order_id}, user_tg_id={user_tg_id})"
                )
            finally:
                await shop_bot.session.close()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _delete_topic_safe(callback.bot, order.drop_group_chat_id, order.drop_topic_id)
    await callback.answer("Готово ✅")


@router.callback_query(F.data.startswith("order_refund:"))
async def order_refund_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    parsed = _parse_two_ids(callback.data, "order_refund")
    if not parsed:
        return await callback.answer("Кнопка устарела. Обновите карточку заказа.", show_alert=True)
    shop_id, order_id = parsed

    order = await order_repo.get_order_by_order_id(shop_id=shop_id, order_id=order_id)
    if not order:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(shop_id=shop_id, order_id=order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может вернуть", show_alert=True)

    try:
        await callback.message.edit_reply_markup(reply_markup=confirm_refund_kb(shop_id, order_id))
    except Exception:
        pass

    await callback.answer("Подтвердите возврат 💸")


@router.callback_query(F.data.startswith("order_refund_confirm:"))
async def order_refund_confirm_clb(
    callback: CallbackQuery,
    order_repo: ShopOrderRepository,
    user_repo: ShopUserRepository,
    shop_repo: ShopRepository,  
):
    parsed = _parse_two_ids(callback.data, "order_refund_confirm")
    if not parsed:
        return await callback.answer("Кнопка устарела. Обновите карточку заказа.", show_alert=True)
    shop_id, order_id = parsed

    order = await order_repo.get_order_by_order_id(shop_id=shop_id, order_id=order_id)
    if not order:
        return await callback.answer("Заказ не найден", show_alert=True)

    executor_tg_id = await order_repo.get_executor_tg_id(shop_id=shop_id, order_id=order_id)
    if executor_tg_id != callback.from_user.id:
        return await callback.answer("Только исполнитель может вернуть", show_alert=True)

    user_tg_id = await _get_user_tg_id_safe(order_repo, shop_id, order_id, order_obj=order)
    if not user_tg_id:
        return await callback.answer("Не найден tg_id пользователя", show_alert=True)

    await user_repo.increase_balance(shop_id=order.shop_id, tg_id=user_tg_id, amount=order.price)
    await order_repo.set_status(shop_id=shop_id, order_id=order_id, status="refunded")

    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
    if shop and getattr(shop, "bot_token", None):
        from aiogram import Bot
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties

        shop_bot = Bot(
            token=shop.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
        )
        try:
            await shop_bot.send_message(
                chat_id=user_tg_id,
                text=(
                    "<b>Возврат выполнен</b>\n\n"
                    f"По заказу <b>{order_id}</b> оформлен возврат.\n"
                    f"Сумма <b>{order.price}</b> руб. возвращена на ваш баланс.\n\n"
                    "Если остались вопросы - напишите в поддержку."
                ),
                reply_markup=support_chat_kb(),
            )
        except Exception as e:
            logger.exception(
                f"Failed to notify user about refund: {e} "
                f"(shop_id={shop_id}, order_id={order_id}, user_tg_id={user_tg_id})"
            )
        finally:
            await shop_bot.session.close()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _delete_topic_safe(callback.bot, order.drop_group_chat_id, order.drop_topic_id)
    await callback.answer("Возврат выполнен", show_alert=True)


async def _delete_topic_safe(bot, group_chat_id: int | None, topic_id: int | None):
    if not group_chat_id or not topic_id:
        return
    try:
        await bot.delete_forum_topic(chat_id=group_chat_id, message_thread_id=topic_id)
    except Exception:
        try:
            await bot.close_forum_topic(chat_id=group_chat_id, message_thread_id=topic_id)
        except Exception:
            pass
