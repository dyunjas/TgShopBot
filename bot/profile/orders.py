from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import back_main_menu_kb, build_orders_kb, back_to_orders_bt

router = Router()

PAGE_LIST = "orders_menu"
PAGE_ITEM = "order_item_menu"


def _caption(page, fallback: str) -> str:
    if not page:
        return fallback
    title = page.title or ""
    body = page.content or ""
    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return title or body or fallback


@router.callback_query(F.data == "order_history")
async def orders_clb(
    callback: CallbackQuery,
    shop_id: int,
    order_repo: ShopOrderRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    orders = await order_repo.get_orders(shop_id=shop_id, tg_id=tg_id)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_LIST)
    caption_no = _caption(page, "У вас пока нет заказов")
    caption_yes = _caption(page, "Ваши заказы:")
    image = page.image if page else None

    if not orders:
        if image:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption_no, parse_mode="HTML"),
                reply_markup=back_main_menu_kb(),
            )
        else:
            await callback.message.edit_text(caption_no, parse_mode="HTML", reply_markup=back_main_menu_kb())
        await callback.answer()
        return

    kb = build_orders_kb(orders, page=0).as_markup()
    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption_yes, parse_mode="HTML"),
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(caption_yes, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data.startswith("orders_page:"))
async def paginate_orders_clb(
    callback: CallbackQuery,
    shop_id: int,
    order_repo: ShopOrderRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    page_num = int(callback.data.split(":")[1])
    orders = await order_repo.get_orders(shop_id=shop_id, tg_id=tg_id)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_LIST)
    caption = _caption(page, "Ваши заказы:")
    image = page.image if page else None

    if not orders:
        caption = _caption(page, "У вас пока нет заказов")
        if image:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
                reply_markup=back_main_menu_kb(),
            )
        else:
            await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=back_main_menu_kb())
        await callback.answer()
        return

    kb = build_orders_kb(orders, page=page_num).as_markup()
    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data.startswith("order:"))
async def order_detail_clb(
    callback: CallbackQuery,
    shop_id: int,
    order_repo: ShopOrderRepository,
    page_repo: ShopPageRepository,
):
    parts = callback.data.split(":")
    order_db_id = int(parts[1])
    page_num = int(parts[2]) if len(parts) > 2 else 0

    order = await order_repo.get_order_by_id(shop_id=shop_id, order_db_id=order_db_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    text = (
        f"<b>Заказ:</b> {order.title}\n"
        f"<b>Цена:</b> {order.price} RUB\n"
        f"<b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M') if order.created_at else '-'}\n"
        f"<b>ID заказа:</b> <code>{order.order_id}</code>"
    )

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ITEM)
    image = page.image if page else None

    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=text, parse_mode="HTML"),
            reply_markup=back_to_orders_bt(page_num),
        )
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_orders_bt(page_num))

    await callback.answer()
