from aiogram import Router, F
from aiogram.types import CallbackQuery

from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import back_main_menu_kb, build_orders_kb, back_to_orders_bt
from bot.utils.media_fallback import safe_edit_photo_or_text

router = Router()

PAGE_LIST = "orders_menu"
PAGE_ITEM = "order_item_menu"


def _format_template(tpl: str, values: dict[str, object]) -> str:
    if not tpl:
        return ""
    out = tpl
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _caption(page, fallback: str, values: dict[str, object] | None = None) -> str:
    values = values or {}

    if not page:
        return _format_template(fallback, values)

    title = ((page.title or "").strip())
    body = ((page.content or "").strip())

    title = _format_template(title, values)
    body = _format_template(body, values)

    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return body or (f"<b>{title}</b>" if title else _format_template(fallback, values))


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
    image = page.image if page else None

    if not orders:
        caption_no = _caption(page, "У вас пока нет заказов")
        await safe_edit_photo_or_text(
            message=callback.message,
            image=image,
            text=caption_no,
            parse_mode="HTML",
            reply_markup=back_main_menu_kb(),
        )
        await callback.answer()
        return

    caption_yes = _caption(page, "Ваши заказы:")
    kb = build_orders_kb(orders, page=0).as_markup()

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=caption_yes,
        parse_mode="HTML",
        reply_markup=kb,
    )

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
    image = page.image if page else None

    if not orders:
        caption = _caption(page, "У вас пока нет заказов")
        await safe_edit_photo_or_text(
            message=callback.message,
            image=image,
            text=caption,
            parse_mode="HTML",
            reply_markup=back_main_menu_kb(),
        )
        await callback.answer()
        return

    caption = _caption(page, "Ваши заказы:")
    kb = build_orders_kb(orders, page=page_num).as_markup()

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=caption,
        parse_mode="HTML",
        reply_markup=kb,
    )

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

    created_at_text = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "-"

    values = {
        "order_title": getattr(order, "title", "-"),
        "price": getattr(order, "price", "-"),
        "created_at": created_at_text,
        "order_id": getattr(order, "order_id", "-"),
    }

    fallback = (
        f"<b>Заказ:</b> {values['order_title']}\n"
        f"<b>Цена:</b> {values['price']} RUB\n"
        f"<b>Дата:</b> {values['created_at']}\n"
        f"<b>ID заказа:</b> <code>{values['order_id']}</code>"
    )

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ITEM)
    text = _caption(page, fallback, values=values)
    image = page.image if page else None

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=text,
        parse_mode="HTML",
        reply_markup=back_to_orders_bt(page_num),
    )

    await callback.answer()
