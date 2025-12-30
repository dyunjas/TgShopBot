from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from backend.repositories.shop_repository import ShopRepository

async def build_shop_keyboard(shop_repo: ShopRepository, parent_id: int | None = None):
    builder = InlineKeyboardBuilder()

    categories = await shop_repo.get_categories(parent_id=parent_id)
    for cat in categories:
        builder.button(
        text=f"📂 {cat.title}",
        callback_data=f"category:{cat.id}"
        )

    if parent_id:
        items = await shop_repo.get_items_by_category(parent_id)
        for item in items:
            builder.button(
                text=f"{item.title}",
                callback_data=f"item:{item.id}"
            )
    builder.adjust(2)

    if parent_id is None:
        builder.row(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    else:
        current_category = await shop_repo.get_category_by_id(parent_id)
        if current_category and current_category.parent_id:

            builder.row(InlineKeyboardButton(text="Назад", callback_data=f"category:{current_category.parent_id}"))
        else:
            builder.row(InlineKeyboardButton(text="Назад", callback_data="shop"))
    return builder

def build_item_kb(item_id: int, category_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(text="Купить", callback_data=f"confirm_purchase:{item_id}")
    builder.button(text="Назад", callback_data=f"category:{category_id}")
    builder.adjust(1, 1)
    return builder.as_markup()