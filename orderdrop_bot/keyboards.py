from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def take_order_kb(shop_id: int, order_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Взять заказ", callback_data=f"order_take:{shop_id}:{order_id}")
    return kb.as_markup()


def order_in_work_kb(shop_id: int, order_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершить", callback_data=f"order_done:{shop_id}:{order_id}")
    kb.button(text="💸 Возврат", callback_data=f"order_refund:{shop_id}:{order_id}")
    kb.adjust(2)
    return kb.as_markup()


def confirm_done_kb(shop_id: int, order_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, завершить", callback_data=f"order_done_confirm:{shop_id}:{order_id}")
    kb.button(text="↩️ Назад", callback_data=f"order_inwork_back:{shop_id}:{order_id}")
    kb.adjust(1)
    return kb.as_markup()


def confirm_refund_kb(shop_id: int, order_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💸 Да, вернуть", callback_data=f"order_refund_confirm:{shop_id}:{order_id}")
    kb.button(text="↩️ Назад", callback_data=f"order_inwork_back:{shop_id}:{order_id}")
    kb.adjust(1)
    return kb.as_markup()


def rate_kb(shop_id: int, order_id: str) -> InlineKeyboardMarkup:

    kb = InlineKeyboardBuilder()
    for i in range(5, 0, -1):
        kb.button(text=("⭐" * i), callback_data=f"rate:{shop_id}:{order_id}:{i}")
    kb.adjust(1, 1, 1, 1, 1)
    return kb.as_markup()
