from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_profile_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def payment_choice_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="СБП 1", callback_data="pay_pally")
    builder.button(text="СБП 2", callback_data="pay_lava")
    builder.adjust(1, 1)
    return builder.as_markup()


def payment_menu_kb(*, invoice_url: str, invoice_id: str, check_prefix: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", url=invoice_url)
    builder.button(text="🔄 Проверить оплату", callback_data=f"{check_prefix}:{invoice_id}")
    builder.adjust(1, 1)
    return builder.as_markup()
