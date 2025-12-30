from aiogram.utils.keyboard import InlineKeyboardBuilder

def back_admin_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Админ меню", callback_data="admin_menu")
    return builder.as_markup()

def admin_menu_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="💳 История транзакций", callback_data="admin_transactions")
    builder.button(text="📦 История заказов", callback_data="admin_orders")
    builder.button(text="✉️ Создать рассылку", callback_data="admin_broadcast")
    builder.button(text="⚙️ Добавить товар/категорию", callback_data="create_category_item")
    builder.button(text="⚙️ Удалить товар/категорию", callback_data="delete_category_item")
    builder.adjust(1, 1, 1)
    return builder.as_markup()