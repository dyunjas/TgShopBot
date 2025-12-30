from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import AdminShopStates
from backend.repositories.shop_repository import ShopRepository

from .keyboards import categories_kb, admin_menu_create_kb, admin_menu_back_kb, create_category_item_kb

from backend.images.images_url import ADMIN_MENU_URL

router = Router()

@router.callback_query(F.data == "create_category_item")
async def create_category_item(callback: CallbackQuery):
    text = "Выберите действие:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=create_category_item_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "create_item")
async def start_create_item(callback: CallbackQuery, state: FSMContext, shop_repo: ShopRepository):
    categories = await shop_repo.get_all_categories()
    if not categories:
        await callback.answer("❌ Нет категорий для добавления товара", show_alert=True)
        return
    
    text = "Выберите категорию или подкатегорию для товара"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=categories_kb(categories)
    )
    await state.set_state(AdminShopStates.choosing_category)
    await callback.answer()

@router.callback_query(AdminShopStates.choosing_category, F.data.startswith("category:"))
async def choose_item_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)

    text = "Введите название товара:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_item_name)
    await callback.answer()

@router.message(AdminShopStates.entering_item_name)
async def item_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text, type="item")
    text = "Введите цену товара (<b>СТРОГО</b> целое число):"
    await message.answer(
        text=text,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_item_price)

@router.message(AdminShopStates.entering_item_price)
async def item_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
    except ValueError:
        text = "❌ Введите число"
        await message.answer(
            text=text,
        reply_markup=admin_menu_create_kb()
        )
        return
    
    await state.update_data(price=price)
    text = "Введите описание товара:"
    await message.answer(
        text=text,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_item_description)


@router.message(AdminShopStates.entering_item_description)
async def item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    text = "Отправьте ссылку на картинку для товара:"
    await message.answer(
        text=text,
        reply_markup=admin_menu_create_kb()
    )
    await state.set_state(AdminShopStates.entering_item_img)


@router.message(AdminShopStates.entering_item_img)
async def item_img(message: Message, state: FSMContext, shop_repo: ShopRepository):
    data = await state.get_data()

    if data.get("type") != "item":
        return

    if message.photo:
        img_url = message.photo[-1].file_id
    else:
        img_url = message.text

    await shop_repo.create_item(
        title=data["title"],
        price=data["price"],
        description=data["description"],
        img=img_url,
        category_id=data["category_id"]
    )

    text = f"Товар <b>{data['title']}</b> создан ✅"
    await message.answer(
        text=text,
        reply_markup=admin_menu_back_kb()
    )
    await state.clear()