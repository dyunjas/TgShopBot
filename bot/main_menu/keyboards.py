from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Магазин🎮", callback_data="shop")
    builder.button(text="Кабинет🪪", callback_data="profile")
    builder.button(text="Частые вопросы⁉️", callback_data="questions")
    builder.button(text="Гарантии☑️", callback_data="guarantees")
    builder.button(text="Отзывы🗣", callback_data="reviews")
    builder.button(text="Поддержка👨🏼‍💻", callback_data="support")
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def back_main_menu_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()