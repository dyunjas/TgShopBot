from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.images.images_url import QUESTIONS_MENU_URL

from .keyboards import back_main_menu_kb

router = Router()

@router.callback_query(F.data == "questions")
async def guarantees_clb(callback: CallbackQuery):
    
    text = (
        "Ответы на частые вопросы вы можете найти <a href='https://telegra.ph/Otvety-na-voprosy-05-04-10'>тут</a>"
    )

    content = InputMediaPhoto(
        media=QUESTIONS_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_main_menu_kb()
    )
    await callback.answer()