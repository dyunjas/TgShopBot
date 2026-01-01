from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.shop_repository import ShopRepository
from backend.database.models import ShopCategory

from .keyboards import build_shop_keyboard, build_item_kb

router = Router()


@router.callback_query(F.data.startswith("category:"))
async def category_clb(
    callback: CallbackQuery,
    shop_id: int,
    shop_repo: ShopRepository,
):
    category_id = int(callback.data.split(":", 1)[1])

    category: ShopCategory | None = await shop_repo.get_category_by_id(
        shop_id=shop_id,
        category_id=category_id,
    )
    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    kb = await build_shop_keyboard(shop_id=shop_id, shop_repo=shop_repo, parent_id=category.id)

    text = "Выберите категорию:" if category.parent_id is None else "Выберите товар:"
    content = InputMediaPhoto(media=category.img, caption=text)

    await callback.message.edit_media(media=content, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("item:"))
async def item_clb(
    callback: CallbackQuery,
    shop_id: int,
    shop_repo: ShopRepository,
):
    item_id = int(callback.data.split(":", 1)[1])

    item = await shop_repo.get_item_by_id(shop_id=shop_id, item_id=item_id)
    if not item:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"<b>Товар:</b> {item.title}\n"
        f"<b>Цена:</b> {item.price} RUB\n\n"
        f"<b>Описание:</b> {item.description or '-'}"
    )

    content = InputMediaPhoto(media=item.img, caption=text, parse_mode="HTML")

    await callback.message.edit_media(
        media=content,
        reply_markup=build_item_kb(item_id=item.id, category_id=item.category_id),
    )
    await callback.answer()
