from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

CATEGORIES_PER_PAGE = 10
ITEMS_PER_PAGE = 10


def admin_menu_create_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Отменить", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def admin_menu_back_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def categories_kb(categories: list, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * CATEGORIES_PER_PAGE
    end = start + CATEGORIES_PER_PAGE
    chunk = categories[start:end]

    for category in chunk:
        title = f"{category.parent.title}/{category.title}" if category.parent else category.title
        builder.button(text=title, callback_data=f"category:{category.id}")
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"category_page:{page-1}"))
    if end < len(categories):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"category_page:{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="Админ меню", callback_data="admin_menu"))

    return builder.as_markup()

def create_category_item_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить категорию", callback_data="create_category")
    builder.button(text="➕ Добавить подкатегорию", callback_data="create_subcategory")
    builder.button(text="➕ Добавить товар", callback_data="create_item")
    builder.button(text="Админ меню", callback_data="admin_menu")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def categories_delete_kb(categories: list, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * CATEGORIES_PER_PAGE
    end = start + CATEGORIES_PER_PAGE
    chunk = categories[start:end]

    for category in chunk:
        title = (
            f"🗑 {category.parent.title}/{category.title}"
            if category.parent else f"🗑 {category.title}"
        )
        builder.button(text=title, callback_data=f"delcat:{category.id}:{page}")
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"delcat_page:{page-1}"))
    if end < len(categories):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"delcat_page:{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="Админ меню", callback_data="admin_menu"))
    return builder.as_markup()

def items_delete_kb(items: list, page: int = 0):
    builder = InlineKeyboardBuilder()

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    chunk = items[start:end]

    for item in chunk:
        category_title = item.category.title
        if item.category.parent:
            category_title = f"{item.category.parent.title}/{category_title}"
        title = f"🗑 {category_title}/{item.title}"
        builder.button(text=title, callback_data=f"delitem:{item.id}:{page}")
    builder.adjust(1)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"delitem_page:{page-1}"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд", callback_data=f"delitem_page:{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="Админ меню", callback_data="admin_menu"))
    return builder.as_markup()


def delete_category_item_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="➖ Удалить категорию", callback_data="delete_category")
    builder.button(text="➖ Удалить товар", callback_data="delete_item")
    builder.button(text="Админ меню", callback_data="admin_menu")
    builder.adjust(1, 1, 1)
    return builder.as_markup()