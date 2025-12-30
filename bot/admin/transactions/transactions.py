from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.transaction_repository import ShopTransactionRepository

from backend.images.images_url import ADMIN_MENU_URL

from bot.admin.keyboards import back_admin_kb
from .keyboards import build_transaction_admin_kb, back_from_transaction_kb

router = Router()


@router.callback_query(F.data == "admin_transactions")
async def admin_transactions_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    transactions = await transaction_repo.get_all_transactions()

    if not transactions:
        text = "Транзакций пока нет"
        content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
        await callback.message.edit_media(media=content, reply_markup=back_admin_kb())
        await callback.answer()
        return

    keyboard = build_transaction_admin_kb(transactions, page=0)
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption="Все транзакции:")
    await callback.message.edit_media(media=content, reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_transactions_page:"))
async def paginate_transactions_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    page = int(callback.data.split(":")[1])
    transactions = await transaction_repo.get_all_transactions()

    if not transactions:
        text = "Транзакций пока нет"
        content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
        await callback.message.edit_media(media=content, reply_markup=back_admin_kb())
        await callback.answer()
        return

    keyboard = build_transaction_admin_kb(transactions, page=page)
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption="Все транзакции:")
    await callback.message.edit_media(media=content, reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_transaction:"))
async def transaction_detail_clb(callback: CallbackQuery, transaction_repo: ShopTransactionRepository):
    parts = callback.data.split(":")
    transaction_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    transaction = await transaction_repo.get_transaction_by_id(transaction_id)
    if not transaction:
        await callback.answer("Транзакция не найдена", show_alert=True)
        return

    if getattr(transaction, "user", None):
        if getattr(transaction.user, "username", None):
            username = f"@{transaction.user.username}"
        else:
            username = f"ID: {transaction.user.tg_id}"
    else:
        username = "—"

    created_at_text = transaction.created_at.strftime('%d.%m.%Y %H:%M') if transaction.created_at else "-"
    paid_at_text = transaction.paid_at.strftime('%d.%m.%Y %H:%M') if getattr(transaction, "paid_at", None) else "-"
    status_text = "Оплачено" if getattr(transaction, "paid", False) else "Не оплачено"

    text = (
        f"<b>Сумма:</b> {transaction.amount} RUB\n"
        f"<b>Пользователь:</b> {username}\n"
        f"<b>Дата создания:</b> {created_at_text}\n"
        f"<b>Дата оплаты:</b> {paid_at_text}\n"
        f"<b>Статус:</b> {status_text}\n"
        f"<b>Система:</b> {transaction.payment_system}\n"
        f"<b>ID пополнения</b>: <code>{transaction.order_id}</code>\n"
        f"<b>ID транзакции:</b> <code>{transaction.transaction_id}</code>"
    )

    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text, parse_mode="HTML")
    await callback.message.edit_media(
        media=content,
        reply_markup=back_from_transaction_kb(page)
    )
    await callback.answer()