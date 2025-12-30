from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.images.images_url import SUPPORT_MENU_URL

from .keyboards import back_main_menu_kb

router = Router()

@router.callback_query(F.data == "support")
async def guarantees_clb(callback: CallbackQuery):
    
    text = (
        "Вы можете задать свой вопрос в <a href='https://t.me/ShopsSupport_bot'>поддержку</a>. Но перед этим рекомендуем ознакомиться с нашим FAQ"
    )

    content = InputMediaPhoto(
        media=SUPPORT_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_main_menu_kb()
    )
    await callback.answer()