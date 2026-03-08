from aiogram import Router, F
from aiogram.types import CallbackQuery

from backend.repositories.shop_repository import ShopRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import build_shop_keyboard
from bot.utils.media_fallback import safe_edit_photo_or_text

router = Router()

PAGE_SHOP_MENU = "shop_menu"


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


@router.callback_query(F.data == "shop")
async def shop_clb(
    callback: CallbackQuery,
    shop_id: int,
    shop_repo: ShopRepository,
    page_repo: ShopPageRepository,
):
    kb = await build_shop_keyboard(shop_id=shop_id, shop_repo=shop_repo, parent_id=None)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_SHOP_MENU)
    caption = _caption(page, "Активные категории:")
    image = page.image if page else None

    await safe_edit_photo_or_text(
        message=callback.message,
        image=image,
        text=caption,
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
    )

    await callback.answer()
