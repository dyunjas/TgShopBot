from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.repositories.shop_repository import ShopRepository
from backend.images.images_url import ADMIN_MENU_URL

from .keyboards import items_delete_kb, categories_delete_kb, delete_category_item_kb

router = Router()

@router.callback_query(F.data == "delete_category_item")
async def create_category_item(callback: CallbackQuery):
    text = "Выберите действие:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=delete_category_item_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "delete_category")
async def show_delete_categories(callback: CallbackQuery, shop_repo: ShopRepository):
    categories = await shop_repo.get_all_categories()
    if not categories:
        await callback.answer("❌ Нет категорий", show_alert=True)
        return

    text = "Выберите категорию для удаления:"
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
    await callback.message.edit_media(
        media=content,
        reply_markup=categories_delete_kb(categories, page=0)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delcat:"))
async def delete_category(callback: CallbackQuery, shop_repo: ShopRepository):
    category_id = int(callback.data.split(":")[1])
    category = await shop_repo.get_category_by_id(category_id)
    success = await shop_repo.delete_category(category_id)

    if not success:
        await callback.answer("❌ В категории есть товары или подкатегории. Сначала удалите их.", show_alert=True)
        return

    await shop_repo.delete_category(category_id)

    await callback.answer(f"✅ Категория {category.title} удалена", show_alert=True)

    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption="Выберите действие:"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=delete_category_item_kb()
    )

@router.callback_query(F.data == "delete_item")
async def show_delete_items(callback: CallbackQuery, shop_repo: ShopRepository):
    items = await shop_repo.get_items()
    if not items:
        await callback.answer("❌ Нет товаров", show_alert=True)
        return

    text = "Выберите товар для удаления:"
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
    await callback.message.edit_media(
        media=content,
        reply_markup=items_delete_kb(items, page=0)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delitem:"))
async def delete_item(callback: CallbackQuery, shop_repo: ShopRepository):
    item_id = int(callback.data.split(":")[1])
    item = await shop_repo.get_item_by_id(item_id)
    await shop_repo.delete_item(item_id)

    await callback.answer(f"✅ Товар {item.title} удален", show_alert=True)

    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption="Выберите действие:"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=delete_category_item_kb()
    )

@router.callback_query(F.data.startswith("delitem_page:"))
async def paginate_items(callback: CallbackQuery, shop_repo: ShopRepository):
    page = int(callback.data.split(":")[1])
    items = await shop_repo.get_items()

    text = "Выберите товар для удаления:"
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
    await callback.message.edit_media(
        media=content,
        reply_markup=items_delete_kb(items, page=page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delcat_page:"))
async def paginate_categories(callback: CallbackQuery, shop_repo: ShopRepository):
    page = int(callback.data.split(":")[1])
    categories = await shop_repo.get_all_categories()

    text = "Выберите категорию для удаления:"
    content = InputMediaPhoto(media=ADMIN_MENU_URL, caption=text)
    await callback.message.edit_media(
        media=content,
        reply_markup=categories_delete_kb(categories, page=page)
    )
    await callback.answer()