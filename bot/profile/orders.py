from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.order_repository import ShopOrderRepository

from backend.images.images_url import ORDERS_MENU_URL, ORDER_ITEM_MENU_URL

from .keyboards import back_main_menu_kb, build_orders_kb, back_to_orders_bt


router = Router()

@router.callback_query(F.data == "order_history")
async def orders_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    tg_id = callback.from_user.id
    orders = await order_repo.get_orders(tg_id)

    content = InputMediaPhoto(
        media=ORDERS_MENU_URL,
        caption="У вас пока нет заказов"
    )
    content_2 = InputMediaPhoto(
        media=ORDERS_MENU_URL,
        caption="Ваши заказы:"
    )
    if not orders:
        await callback.message.edit_media(
            media=content,
            reply_markup=back_main_menu_kb()
        )
        await callback.answer()
        return
    keyboard = build_orders_kb(orders, page=0)
    await callback.message.edit_media(
        media=content_2,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("orders_page:"))
async def paginate_orders_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    tg_id = callback.from_user.id
    page = int(callback.data.split(":")[1])
    orders = await order_repo.get_orders(tg_id)

    if not orders:
        content = InputMediaPhoto(
            media=ORDERS_MENU_URL,
            caption="У вас пока нет заказов"
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=back_main_menu_kb()
        )
        await callback.answer()
        return

    keyboard = build_orders_kb(orders, page=page)
    content = InputMediaPhoto(
        media=ORDERS_MENU_URL,
        caption="Ваши заказы:"
    )

    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("order:"))
async def order_detail_clb(callback: CallbackQuery, order_repo: ShopOrderRepository):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    stmt = await order_repo.get_order_by_id(order_id)
    if not stmt:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    text = (
        f"<b>Заказ:</b> {stmt.title}\n"
        f"<b>Цена:</b> {stmt.price} RUB\n"
        f"<b>Дата:</b> {stmt.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"<b>ID заказа:</b> {stmt.order_id}"
    )
    content = InputMediaPhoto(
        media=ORDER_ITEM_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )


    await callback.message.edit_media(
        media=content,
        reply_markup=back_to_orders_bt(page)
    )
    await callback.answer()