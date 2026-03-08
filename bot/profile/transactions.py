from aiogram import Router, F
from aiogram.types import CallbackQuery

from backend.repositories.transaction_repository import ShopTransactionRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import back_main_menu_kb, build_transactions_kb, back_to_transactions_bt
from bot.utils.media_fallback import safe_edit_photo_or_text

router = Router()

PAGE_LIST = "transactions_menu"
PAGE_ITEM = "transaction_item_menu"


def _format_template(tpl: str, values: dict[str, object]) -> str:
    """Простой шаблонизатор для {key}. Не падает если ключа нет."""
    if not tpl:
        return ""
    out = tpl
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _caption(page, fallback: str, values: dict[str, object] | None = None) -> str:
    """
    Возвращает caption из page.title/page.content.
    Если title пустой — заголовок НЕ показываем вообще.
    """
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


@router.callback_query(F.data == "transaction_history")
async def transactions_clb(
    callback: CallbackQuery,
    shop_id: int,
    transaction_repo: ShopTransactionRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    txs = await transaction_repo.get_transactions(shop_id=shop_id, tg_id=tg_id)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_LIST)
    image = page.image if page else None

    if not txs:
        caption = _caption(page, "У вас пока нет транзакций")
        await safe_edit_photo_or_text(
            message=callback.message,
            image=image,
            text=caption,
            parse_mode="HTML",
            reply_markup=back_main_menu_kb(),
        )
        await callback.answer()
        return

    caption = _caption(page, "Ваши транзакции:")
    kb = build_transactions_kb(txs, page=0).as_markup()

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=caption,
        parse_mode="HTML",
        reply_markup=kb,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("transactions_page:"))
async def transactions_page_clb(
    callback: CallbackQuery,
    shop_id: int,
    transaction_repo: ShopTransactionRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    page_num = int(callback.data.split(":")[1])
    txs = await transaction_repo.get_transactions(shop_id=shop_id, tg_id=tg_id)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_LIST)
    image = page.image if page else None

    if not txs:
        caption = _caption(page, "У вас пока нет транзакций")
        await safe_edit_photo_or_text(
            message=callback.message,
            image=image,
            text=caption,
            parse_mode="HTML",
            reply_markup=back_main_menu_kb(),
        )
        await callback.answer()
        return

    caption = _caption(page, "Ваши транзакции:")
    kb = build_transactions_kb(txs, page=page_num).as_markup()

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=caption,
        parse_mode="HTML",
        reply_markup=kb,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("transaction:"))
async def transaction_detail_clb(
    callback: CallbackQuery,
    shop_id: int,
    transaction_repo: ShopTransactionRepository,
    page_repo: ShopPageRepository,
):
    parts = callback.data.split(":")
    transaction_db_id = int(parts[1])
    page_num = int(parts[2]) if len(parts) > 2 else 0

    tx = await transaction_repo.get_transaction_by_id(shop_id=shop_id, transaction_db_id=transaction_db_id)
    if not tx:
        await callback.answer("Транзакция не найдена", show_alert=True)
        return

    created_at_text = tx.created_at.strftime("%d.%m.%Y %H:%M") if tx.created_at else "-"
    paid_at_text = tx.paid_at.strftime("%d.%m.%Y %H:%M") if getattr(tx, "paid_at", None) else "-"
    status_text = "Оплачено" if getattr(tx, "paid", False) else "Не оплачено"

    values = {
        "amount": tx.amount,
        "created_at": created_at_text,
        "paid_at": paid_at_text,
        "status": status_text,
        "payment_system": getattr(tx, "payment_system", "-"),
        "order_id": getattr(tx, "order_id", "-"),
        "transaction_id": getattr(tx, "transaction_id", "-"),
    }

    fallback = (
        f"<b>Сумма:</b> {values['amount']} RUB\n"
        f"<b>Дата создания:</b> {values['created_at']}\n"
        f"<b>Дата оплаты:</b> {values['paid_at']}\n"
        f"<b>Статус:</b> {values['status']}\n"
        f"<b>Система:</b> {values['payment_system']}\n"
        f"<b>ID пополнения:</b> <code>{values['order_id']}</code>\n"
        f"<b>ID транзакции:</b> <code>{values['transaction_id']}</code>"
    )

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ITEM)
    text = _caption(page, fallback, values=values)
    image = page.image if page else None

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=text,
        parse_mode="HTML",
        reply_markup=back_to_transactions_bt(page_num),
    )

    await callback.answer()
