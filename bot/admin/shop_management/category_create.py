from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import AdminShopStates
from backend.repositories.shop_repository import ShopRepository

from backend.images.images_url import ADMIN_MENU_URL

from .keyboards import admin_menu_create_kb, admin_menu_back_kb


router = Router()

@router.callback_query(F.data == "create_category")
async def start_create_category_clb(callback: CallbackQuery, state: FSMContext):
    text = "Введите название категории:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_category_name)
    await callback.answer()

@router.message(AdminShopStates.entering_category_name)
async def category_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text, type="category")
    text = "Отправьте ссылку на картинку для категории:"
    await message.answer(
        text=text,
        reply_markup=admin_menu_create_kb()
        )
    await state.set_state(AdminShopStates.entering_category_img)

@router.message(AdminShopStates.entering_category_img)
async def category_image(message: Message, state: FSMContext, shop_repo: ShopRepository):
    data = await state.get_data()

    img_url = message.text

    await shop_repo.create_category(title=data["title"], img=img_url, parent_id=None)
    text = f" ✅ Категория <b>{data['title']}</b> создана"
    await message.answer(
        text=text,
        reply_markup=admin_menu_back_kb()
        )
    await state.clear()
    