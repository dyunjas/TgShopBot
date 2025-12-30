from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

ORDERS_PER_PAGE = 5

def build_order_admin_kb(orders, page: int = 0):
    builder = InlineKeyboardBuilder()
    
    start = page * ORDERS_PER_PAGE
    end = start + ORDERS_PER_PAGE
    chunk = orders[start:end]

    for order in chunk:
        builder.button(
            text=f"📦{order.title} [{order.order_id}]",
            callback_data=f"admin_order:{order.id}:{page}"
        )
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"admin_orders_page:{page-1}"))
    if end < len(orders):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"admin_orders_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="Админ меню", callback_data="admin_menu"))
    return builder

def back_from_order_kb(page):
    builder = InlineKeyboardBuilder()

    builder.button(text="Назад", callback_data=f"admin_orders_page:{page}")
    return builder.as_markup()