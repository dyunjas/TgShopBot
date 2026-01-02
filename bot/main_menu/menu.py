from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import main_menu_kb

router = Router()

MAIN_MENU_TYPE = "main_menu"


def _build_caption(page, fallback_text: str) -> str:
    if not page:
        return fallback_text

    title = (page.title or "").strip()
    body = (page.content or "").strip()

    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    if title:
        return f"<b>{title}</b>"
    if body:
        return body
    return fallback_text


@router.message(Command("start"))
async def start_cmd(
    message: Message,
    *,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=MAIN_MENU_TYPE)

    caption = _build_caption(page, "Главное меню")
    img = page.image if page else None

    if img:
        await message.answer_photo(
            photo=img,
            caption=caption,
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(
            text=caption,
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "main_menu")
async def main_menu_clb(
    callback: CallbackQuery,
    *,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=MAIN_MENU_TYPE)

    caption = _build_caption(page, "Главное меню")
    img = page.image if page else None

    if img:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=img, caption=caption, parse_mode="HTML"),
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )

    await callback.answer()
