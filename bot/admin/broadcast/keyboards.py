from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ITEMS_PER_PAGE = 10

def broadcast_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Подтвердить и отправить", callback_data="broadcast_confirm")
    builder.button(text="Отменить", callback_data="broadcast_cancel")
    builder.adjust(1, 1)
    return builder.as_markup()

def cancell_broadcast_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Отменить", callback_data="admin_menu")
    builder.adjust(1, 1)
    return builder.as_markup()

def build_broadcast_bt():
    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить кнопку", callback_data="broadcast_add_button")
    builder.button(text="➡️ Продолжить", callback_data="broadcast_skip_buttons")
    builder.adjust(1)
    return builder.as_markup()

def build_items_cat_kb(items, target_type: str, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    chunk = items[start:end]

    for item in chunk:
        title = f"{item.parent.title}/{item.title}" if hasattr(item, "parent") and item.parent else item.title
        builder.button(
            text=title,
            callback_data=f"btn:{target_type}:{item.id}:{page}"
        )
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"paginate:{target_type}:{page-1}"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"paginate:{target_type}:{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()