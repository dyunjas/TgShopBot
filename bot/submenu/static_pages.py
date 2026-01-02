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
    if body:
        return body
    if title:
        return f"<b>{title}</b>"
    return fallback


async def _render_page(
    callback: CallbackQuery,
    *,
    shop_id: int,
    page_type: str,
    page_repo: ShopPageRepository,
    fallback_text: str,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=page_type)
    text = _caption(page, fallback_text)
    image = page.image if page else None

    message = callback.message

    if image:
        await message.edit_media(
            media=InputMediaPhoto(
                media=image,
                caption=text,
                parse_mode="HTML",
            ),
            reply_markup=back_main_menu_kb(),
        )
    else:

        await message.edit_text(
            text=text,
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
    fallback = "Текст не задан"
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
    fallback = "Текст не задан"
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
    fallback = "Текст не задан"
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
    fallback = "Текст не задан"
    await _render_page(
        callback,
        shop_id=shop_id,
        page_type=PAGE_SUPPORT,
        page_repo=page_repo,
        fallback_text=fallback,
    )
