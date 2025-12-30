from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_msg_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Отправить сообщение", callback_data="support_chat:start")
    return builder.as_markup()

def take_order_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Взять заказ", callback_data=f"order_take:{order_id}")
    return builder.as_markup()


def order_in_work_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Открыть диалог", callback_data=f"order_dialog:{order_id}")
    builder.button(text="✅ Выполнен", callback_data=f"order_done:{order_id}")
    builder.button(text="💸 Вернуть деньги", callback_data=f"order_refund:{order_id}")
    builder.adjust(1, 1, 1)
    return builder.as_markup()


def rate_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    for i in range(5, 0, -1):
        builder.button(text=("⭐" * i), callback_data=f"rate:{order_id}:{i}")
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()
