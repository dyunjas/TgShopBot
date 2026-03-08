from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup

from backend.repositories.shop_repository import ShopRepository
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.order_repository import ShopOrderRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from backend.core.logger_config import logger

from .keyboards import insufficient_funds_kb, support_chat_kb

router = Router()

PAGE_SUCCESS = "purchase_success"
PAGE_INSUFFICIENT = "purchase_insufficient"


def _caption(page, fallback: str) -> str:
    if not page:
        return fallback
    title = (page.title or "").strip()
    body = (page.content or "").strip()
    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return title or body or fallback


async def _edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    msg = callback.message
    if msg is None:
        await callback.answer()
        return

    try:
        if msg.text is not None:
            await msg.edit_text(text, reply_markup=reply_markup)
        elif msg.caption is not None:
            await msg.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await msg.answer(text, reply_markup=reply_markup)

    except TelegramBadRequest as e:
        logger.warning(f"Edit failed, sending new message: {e}")
        await msg.answer(text, reply_markup=reply_markup)

    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase_clb(
    callback: CallbackQuery,
    shop_id: int,
    shop_repo: ShopRepository,
    user_repo: ShopUserRepository,
    order_repo: ShopOrderRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    item_id = int(callback.data.split(":", 1)[1])

    item = await shop_repo.get_item_by_id(shop_id=shop_id, item_id=item_id)
    user = await user_repo.get_user(shop_id=shop_id, tg_id=tg_id)

    if not item or not user:
        await callback.answer("Ошибка покупки", show_alert=True)
        logger.error(f"Purchase error: item or user not found (shop_id={shop_id}, tg_id={tg_id}, item_id={item_id})")
        return

    if user.balance < item.price:
        page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_INSUFFICIENT)
        caption = _caption(page, "Недостаточно средств, пополните баланс")
        await _edit_or_send(callback, text=caption, reply_markup=insufficient_funds_kb())
        logger.info(
            f"[ORDER] purchase_rejected_insufficient shop_id={shop_id} tg_id={tg_id} "
            f"item_id={item_id} price={item.price} balance={user.balance}"
        )
        return

    old_balance = user.balance
    new_balance = await user_repo.decrease_balance(shop_id=shop_id, tg_id=tg_id, amount=item.price)
    await user_repo.increase_orders_amount(shop_id=shop_id, tg_id=tg_id, amount=1)

    order = await order_repo.create_order(shop_id=shop_id, title=item.title, price=item.price, tg_id=tg_id)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_SUCCESS)

    fallback_text = (
        "<b>Оформление заказа</b>\n\n"
        f"Товар: <b>{item.title}</b>\n"
        f"Номер заказа: <b>{order.order_id}</b>\n\n"
        "<i>✅ Заказ был успешно оформлен! Он будет принят сотрудником в порядке очереди. Обычно это занимает не более часа, но зависит от текущей очереди заказов.</i>"
    )

    caption = _caption(page, fallback_text)

    await _edit_or_send(
        callback,
        text=caption
    )

    logger.info(
        f"[ORDER] purchase_success shop_id={shop_id} tg_id={tg_id} item_id={item_id} "
        f"order_id={order.order_id} price={item.price} balance_before={old_balance} balance_after={new_balance}"
    )
