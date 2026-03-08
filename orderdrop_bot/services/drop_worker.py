import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot

from backend.core.config import settings
from backend.core.logger_config import logger
from backend.database.models import ShopOrder
from ..keyboards import take_order_kb

POLL_INTERVAL_SEC = 2


async def publish_new_orders_loop(bot: Bot, session_factory):
    while True:
        try:
            async with session_factory() as session:
                await _publish_batch(bot, session)
                await session.commit()
        except Exception as e:
            logger.exception(f"[DropOrders] publish loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL_SEC)


async def _publish_batch(bot: Bot, session: AsyncSession, limit: int = 10):
    stmt = (
        select(ShopOrder)
        .options(
            selectinload(ShopOrder.user),
            selectinload(ShopOrder.shop),
        )
        .where(
            ShopOrder.status == "paid",
            ShopOrder.drop_topic_id.is_(None),
        )
        .order_by(ShopOrder.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    orders = (await session.execute(stmt)).scalars().all()
    if not orders:
        return

    for order in orders:
        logger.info(
            f"[ORDER] publish_candidate shop_id={order.shop_id} "
            f"order_id={order.order_id} status={order.status} "
            f"user_tg_id={getattr(order.user, 'tg_id', None)}"
        )
        await _publish_one(bot, session, order)


async def _publish_one(bot: Bot, session: AsyncSession, order: ShopOrder):
    shop_title = order.shop.title if order.shop else f"shop_id={order.shop_id}"

    topic = await bot.create_forum_topic(
        chat_id=settings.ORDERS_GROUP_ID,
        name=f"{shop_title} | {order.order_id} | {order.title}",
    )
    topic_id = topic.message_thread_id

    text = (
        "<b>Новый заказ</b>\n\n"
        f"<b>Магазин:</b> {shop_title}\n"
        f"<b>Товар:</b> {order.title}\n"
        f"<b>Цена:</b> {order.price} RUB\n"
        f"<b>Номер заказа:</b> <code>{order.order_id}</code>\n"
        f"<b>Покупатель:</b> <code>{order.user.tg_id}</code>\n"
    )

    msg = await bot.send_message(
        chat_id=settings.ORDERS_GROUP_ID,
        message_thread_id=topic_id,
        text=text,
        reply_markup=take_order_kb(order.shop_id, order.order_id),
    )

    order.drop_group_chat_id = settings.ORDERS_GROUP_ID
    order.drop_topic_id = topic_id
    order.admin_card_msg_id = msg.message_id

    session.add(order)
    logger.info(
        f"[ORDER] published shop_id={order.shop_id} order_id={order.order_id} "
        f"topic_id={topic_id} group_chat_id={settings.ORDERS_GROUP_ID} "
        f"admin_card_msg_id={msg.message_id}"
    )
