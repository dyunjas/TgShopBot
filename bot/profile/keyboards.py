from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

ORDERS_PER_PAGE = 5
TRANSACTIONS_PER_PAGE = 5


def build_orders_kb(orders, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * ORDERS_PER_PAGE
    end = start + ORDERS_PER_PAGE
    chunk = orders[start:end]

    for order in chunk:
        builder.button(
            text=f"📦 {order.title} [{order.order_id}]",
            callback_data=f"order:{order.id}:{page}",
        )
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"orders_page:{page - 1}"))
    if end < len(orders):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"orders_page:{page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="В профиль", callback_data="profile"))
    return builder


def back_to_orders_bt(page: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data=f"orders_page:{page}")
    builder.adjust(1)
    return builder.as_markup()


def build_transactions_kb(transactions, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * TRANSACTIONS_PER_PAGE
    end = start + TRANSACTIONS_PER_PAGE
    chunk = transactions[start:end]

    for tx in chunk:
        builder.button(
            text=f"💳 {tx.amount} RUB",
            callback_data=f"transaction:{tx.id}:{page}",
        )
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"transactions_page:{page - 1}"))
    if end < len(transactions):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"transactions_page:{page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="В профиль", callback_data="profile"))
    return builder


def back_to_transactions_bt(page: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data=f"transactions_page:{page}")
    builder.adjust(1)
    return builder.as_markup()


def profile_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Пополнить баланс💰", callback_data="topup_balance")
    builder.button(text="Использовать промокод🎟️", callback_data="enter_promocode")
    builder.button(text="История покупок🗂️", callback_data="order_history")
    builder.button(text="История транзакций💳", callback_data="transaction_history")
    builder.button(text="Назад", callback_data="main_menu")
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()


def promocode_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def back_promocode_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def back_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
