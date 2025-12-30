from aiogram.types import Message, InputMediaPhoto, CallbackQuery
from aiogram import Router, F
from aiogram.filters import Command

from backend.images.images_url import MAIN_MENU_URL

from .keyboards import main_menu_kb

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):

    text = "Главное меню"
    await message.answer_photo(
        photo=MAIN_MENU_URL,
        caption=text,
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "main_menu")
async def start_clb(callback: CallbackQuery):

    content = InputMediaPhoto(
        media=MAIN_MENU_URL,
        caption="Главное меню"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=main_menu_kb()
    )