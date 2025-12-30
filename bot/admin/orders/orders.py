from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.images.images_url import ADMIN_MENU_URL

from backend.repositories.order_repository import ShopOrderRepository

from .keyboards import build_order_admin_kb, back_from_order_kb

from bot.admin.keyboards import back_admin_kb

router = Router()

@router.callback_query(F.data == "admin_orders")
async def admin_orders_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    orders = await order_repo.get_all_orders()
    if not orders:
        text = "Заказов пока нет"
        content = InputMediaPhoto(
            media=ADMIN_MENU_URL,
            caption=text
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=back_admin_kb()
        )
        await callback.answer()
        return

    keyboard = build_order_admin_kb(orders, page=0)
    text = "Все заказы:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders_page:"))
async def paginate_admin_orders_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    page = int(callback.data.split(":")[1])
    orders = await order_repo.get_all_orders()
    if not orders:
        text = "Заказов пока нет"
        content = InputMediaPhoto(
            media=ADMIN_MENU_URL,
            caption=text
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=back_admin_kb()
        )
        await callback.answer()
        return

    keyboard = build_order_admin_kb(orders, page)
    text = "Все заказы:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order:"))
async def admin_order_detail_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    order = await order_repo.get_order_by_id(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    username = f"@{order.user.username}" if order.user and order.user.username else f"ID: {order.user.tg_id}"
    text = (
        f"🧾 <b>Заказ:</b> {order.title}\n"
        f"💰 <b>Цена:</b> {order.price} RUB\n"
        f"📅 <b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"👤 <b>Пользователь:</b> {username}\n"
        f"🔑 <b>ID заказа:</b> {order.order_id}"
    )

    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_from_order_kb(page)
    )
    await callback.answer()
