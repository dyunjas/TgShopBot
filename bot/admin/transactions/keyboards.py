from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

TRANSACTIONS_PER_PAGE = 5

def build_transaction_admin_kb(transactions, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * TRANSACTIONS_PER_PAGE
    end = start + TRANSACTIONS_PER_PAGE
    chunk = transactions[start:end]

    for transaction in chunk:
        builder.button(
            text=f"💳 {transaction.amount} RUB [{transaction.user_id}]",
            callback_data=f"admin_transaction:{transaction.id}:{page}"
        )
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"admin_transactions_page:{page-1}"))
    if end < len(transactions):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"admin_transactions_page:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="Админ меню", callback_data="admin_menu"))
    return builder

def back_from_transaction_kb(page):
    builder = InlineKeyboardBuilder()

    builder.button(text="Назад", callback_data=f"admin_transactions_page:{page}")
    return builder.as_markup()