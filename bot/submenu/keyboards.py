from aiogram.utils.keyboard import InlineKeyboardBuilder

def back_main_menu_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()