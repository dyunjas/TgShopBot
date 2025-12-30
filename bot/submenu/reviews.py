from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.images.images_url import REVIEWS_MENU_URL

from .keyboards import back_main_menu_kb

router = Router()

@router.callback_query(F.data == "reviews")
async def guarantees_clb(callback: CallbackQuery):
    
    text = (
        "Создали <a href='https://t.me/shopchek_reviews'>чат с отзывами</a>, где публикуются отзывы покупателей"
    )

    content = InputMediaPhoto(
        media=REVIEWS_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_main_menu_kb()
    )
    await callback.answer()