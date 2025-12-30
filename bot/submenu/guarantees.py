from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.images.images_url import GUARANTEES_MENU_URL

from .keyboards import back_main_menu_kb

router = Router()

@router.callback_query(F.data == "guarantees")
async def guarantees_clb(callback: CallbackQuery):
    
    text = (
        "Нажмите на ссылку ниже, чтобы ознакомиться с гарантиями!\n"
        "<a href='https://telegra.ph/Usloviya-polzovaniya-magazinom--SHOPCHEK--SHOPCHQ-SHOPCHQ-bot-02-03'>Ознакомиться с гарантиями</a>"
    )

    content = InputMediaPhoto(
        media=GUARANTEES_MENU_URL,
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_main_menu_kb()
    )
    await callback.answer()