from aiogram import F, Router

from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from backend.core.loader import settings

from backend.images.images_url import ADMIN_MENU_URL

from bot.admin.keyboards import admin_menu_kb

from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("admin_menu"))
async def admin_menu_cmd(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if tg_id not in settings.ADMIN_IDS:
        return

    text = "👑[ADMIN_MENU] Выберите действие:"
    await message.answer_photo(
        photo=ADMIN_MENU_URL,
        caption=text,
        reply_markup=admin_menu_kb()
    )
    await state.clear()


@router.callback_query(F.data == "admin_menu")
async def admin_menu_clb(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    if tg_id not in settings.ADMIN_IDS:
        pass

    text = "👑[ADMIN_MENU] Выберите действие:"
    content = InputMediaPhoto(
        media=ADMIN_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=admin_menu_kb()
    )
    await state.clear()
    await callback.answer()