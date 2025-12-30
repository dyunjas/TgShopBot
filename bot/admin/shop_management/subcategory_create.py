from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import AdminShopStates
from backend.repositories.shop_repository import ShopRepository

from .keyboards import categories_kb, admin_menu_create_kb, admin_menu_back_kb

from backend.images.images_url import ADMIN_MENU_URL

router = Router()


@router.callback_query(F.data == "create_subcategory")
async def start_create_subcategory(callback: CallbackQuery, state: FSMContext, shop_repo: ShopRepository):
    categories = await shop_repo.get_all_categories()
    if not categories:
        await callback.answer("❌ Нет категорий для добавления подкатегории", show_alert=True)
        return
    
    text = "Выберите категорию для добавления подкатегории:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=categories_kb(categories, page=0)
    )
    await state.set_state(AdminShopStates.choosing_subcategory)
    await callback.answer()


@router.callback_query(F.data.startswith("category_page:"))
async def change_category_page(callback: CallbackQuery, state: FSMContext, shop_repo: ShopRepository):
    page = int(callback.data.split(":")[1])
    categories = await shop_repo.get_all_categories()

    await callback.message.edit_reply_markup(
        reply_markup=categories_kb(categories, page=page)
    )
    await callback.answer()


@router.callback_query(AdminShopStates.choosing_subcategory, F.data.startswith("category:"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)

    text = "Введите название подкатегории:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_subcategory_name)
    await callback.answer()


@router.message(AdminShopStates.entering_subcategory_name)
async def subcategory_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text, type="subcategory")
    text = "Отправьте ссылку на картинку для подкатегории:"
    await message.answer(
        text=text,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_subcategory_img)


@router.message(AdminShopStates.entering_subcategory_img)
async def subcategory_img(message: Message, state: FSMContext, shop_repo: ShopRepository):
    data = await state.get_data()

    if data.get("type") != "subcategory":
        return

    img_url = message.text

    await shop_repo.create_category(
        title=data["title"],
        img=img_url,
        parent_id=data["category_id"]
    )

    text = f"✅ Подкатегория <b>{data['title']}</b> создана"
    await message.answer(
        text=text,
        reply_markup=admin_menu_back_kb()
    )
    await state.clear()
