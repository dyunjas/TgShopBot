from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import back_main_menu_kb

router = Router()

PAGE_GUARANTEES = "guarantees"
PAGE_QUESTIONS = "faq" 
PAGE_REVIEWS = "reviews"
PAGE_SUPPORT = "support"


def _caption(page, fallback: str) -> str:
    if not page:
        return fallback
    title = (page.title or "").strip()
    body = (page.content or "").strip()
    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return title or body or fallback


async def _render_page(
    callback: CallbackQuery,
    *,
    shop_id: int,
    page_type: str,
    page_repo: ShopPageRepository,
    fallback_text: str,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=page_type)
    caption = _caption(page, fallback_text)
    image = page.image if page else None

    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
            reply_markup=back_main_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=back_main_menu_kb(),
        )

    await callback.answer()


@router.callback_query(F.data == "guarantees")
async def guarantees_clb(
    callback: CallbackQuery,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    fallback = (
        "Нажмите на ссылку ниже, чтобы ознакомиться с гарантиями!\n"
        "<a href='https://telegra.ph/Usloviya-polzovaniya-magazinom--SHOPCHEK--SHOPCHQ-SHOPCHQ-bot-02-03'>"
        "Ознакомиться с гарантиями</a>"
    )
    await _render_page(
        callback,
        shop_id=shop_id,
        page_type=PAGE_GUARANTEES,
        page_repo=page_repo,
        fallback_text=fallback,
    )


@router.callback_query(F.data == "questions")
async def questions_clb(
    callback: CallbackQuery,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    fallback = "Ответы на частые вопросы вы можете найти <a href='https://telegra.ph/Otvety-na-voprosy-05-04-10'>тут</a>"
    await _render_page(
        callback,
        shop_id=shop_id,
        page_type=PAGE_QUESTIONS,
        page_repo=page_repo,
        fallback_text=fallback,
    )


@router.callback_query(F.data == "reviews")
async def reviews_clb(
    callback: CallbackQuery,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    fallback = "Создали <a href='https://t.me/shopchek_reviews'>чат с отзывами</a>, где публикуются отзывы покупателей"
    await _render_page(
        callback,
        shop_id=shop_id,
        page_type=PAGE_REVIEWS,
        page_repo=page_repo,
        fallback_text=fallback,
    )


@router.callback_query(F.data == "support")
async def support_clb(
    callback: CallbackQuery,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    fallback = (
        "Вы можете задать свой вопрос в <a href='https://t.me/ShopsSupport_bot'>поддержку</a>. "
        "Но перед этим рекомендуем ознакомиться с нашим FAQ"
    )
    await _render_page(
        callback,
        shop_id=shop_id,
        page_type=PAGE_SUPPORT,
        page_repo=page_repo,
        fallback_text=fallback,
    )
