from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_item_kb(item_id: int, category_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(text="Купить", callback_data=f"confirm_purchase:{item_id}")
    builder.button(text="Назад", callback_data=f"category:{category_id}")
    builder.adjust(1, 1)
    return builder.as_markup()

def build_confirm_purchase_kb(item_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(text="Подтверждаю", callback_data=f"confirm_purchase:{item_id}")
    builder.button(text="Отмена", callback_data=f"cancel_purchase:{item_id}")
    builder.adjust(1, 1)
    return builder.as_markup()

def insufficient_funds_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Пополнить баланс", callback_data="profile")
    builder.button(text="Главное меню", callback_data="main_menu")
    builder.adjust(1, 1)
    return builder.as_markup()

def order_support_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Написать в поддержку", url="https://t.me/ShopsSupport_bot")
    builder.adjust(1)
    return builder.as_markup()

def take_order_kb(order_id: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Взять заказ", callback_data=f"order_take:{order_id}")
    return kb.as_markup()