from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.transaction_repository import ShopTransactionRepository

from backend.images.images_url import TRENSACTIONS_MENU_URL, TRANSACTION_ITEM_MENU_URL

from .keyboards import back_main_menu_kb, build_transactions_kb, back_to_transactions_bt


router = Router()


@router.callback_query(F.data == "transaction_history")
async def transactions_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    tg_id = callback.from_user.id
    transactions = await transaction_repo.get_transactions(tg_id)

    if not transactions:
        content = InputMediaPhoto(
            media=TRENSACTIONS_MENU_URL,
            caption="У вас пока нет транзакций"
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=back_main_menu_kb()
        )
        await callback.answer()
        return

    keyboard = build_transactions_kb(transactions, page=0)
    content = InputMediaPhoto(
        media=TRENSACTIONS_MENU_URL,
        caption="Ваши транзакции:"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("transactions_page:"))
async def transaction_orders_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    tg_id = callback.from_user.id
    page = int(callback.data.split(":")[1])
    transactions = await transaction_repo.get_transactions(tg_id)

    if not transactions:
        content = InputMediaPhoto(
            media=TRENSACTIONS_MENU_URL,
            caption="У вас пока нет транзакций"
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=back_main_menu_kb()
        )
        await callback.answer()
        return

    keyboard = build_transactions_kb(transactions, page=page)
    content = InputMediaPhoto(
        media=TRENSACTIONS_MENU_URL,
        caption="Ваши транзакции:"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("transaction:"))
async def transaction_detail_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    parts = callback.data.split(":")
    transaction_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    transaction = await transaction_repo.get_transaction_by_id(transaction_id)
    if not transaction:
        await callback.answer("Транзакция не найдена", show_alert=True)
        return

    created_at_text = transaction.created_at.strftime('%d.%m.%Y %H:%M') if transaction.created_at else "-"
    paid_at_text = transaction.paid_at.strftime('%d.%m.%Y %H:%M') if getattr(transaction, "paid_at", None) else "-"
    status_text = "Оплачено" if getattr(transaction, "paid", False) else "Не оплачено"

    text = (
        f"<b>Сумма:</b> {transaction.amount} RUB\n"
        f"<b>Дата создания:</b> {created_at_text}\n"
        f"<b>Дата оплаты:</b> {paid_at_text}\n"
        f"<b>Статус:</b> {status_text}\n"
        f"<b>Система:</b> {transaction.payment_system}\n"
        f"<b>ID пополнения</b>: <code>{transaction.order_id}</code>\n"
        f"<b>ID транзакции:</b> <code>{transaction.transaction_id}</code>"
    )

    content = InputMediaPhoto(
        media=TRANSACTION_ITEM_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )

    await callback.message.edit_media(
        media=content,
        reply_markup=back_to_transactions_bt(page)
    )
    await callback.answer()
