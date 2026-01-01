from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.transaction_repository import ShopTransactionRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import back_main_menu_kb, build_transactions_kb, back_to_transactions_bt

router = Router()

PAGE_LIST = "transactions_menu"
PAGE_ITEM = "transaction_item_menu"


def _caption(page, fallback: str) -> str:
    if not page:
        return fallback
    title = page.title or ""
    body = page.content or ""
    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return title or body or fallback


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
    caption = _caption(page, "Ваши транзакции:")
    image = page.image if page else None

    if not txs:
        caption = _caption(page, "У вас пока нет транзакций")
        if image:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
                reply_markup=back_main_menu_kb(),
            )
        else:
            await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=back_main_menu_kb())
        await callback.answer()
        return

    kb = build_transactions_kb(txs, page=0).as_markup()
    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=kb)

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
    caption = _caption(page, "Ваши транзакции:")
    image = page.image if page else None

    if not txs:
        caption = _caption(page, "У вас пока нет транзакций")
        if image:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
                reply_markup=back_main_menu_kb(),
            )
        else:
            await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=back_main_menu_kb())
        await callback.answer()
        return

    kb = build_transactions_kb(txs, page=page_num).as_markup()
    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=kb)

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

    text = (
        f"<b>Сумма:</b> {tx.amount} RUB\n"
        f"<b>Дата создания:</b> {created_at_text}\n"
        f"<b>Дата оплаты:</b> {paid_at_text}\n"
        f"<b>Статус:</b> {status_text}\n"
        f"<b>Система:</b> {tx.payment_system}\n"
        f"<b>ID пополнения:</b> <code>{tx.order_id}</code>\n"
        f"<b>ID транзакции:</b> <code>{tx.transaction_id}</code>"
    )

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ITEM)
    image = page.image if page else None

    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=text, parse_mode="HTML"),
            reply_markup=back_to_transactions_bt(page_num),
        )
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_transactions_bt(page_num))

    await callback.answer()
