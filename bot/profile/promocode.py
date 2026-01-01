from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import PromocodeStates
from backend.repositories.promocode_repository import ShopPromocodeRepository
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.shop_page_repository import ShopPageRepository

from .keyboards import promocode_kb, back_promocode_kb

router = Router()

PAGE_PROMO = "promocode_menu"
PAGE_ERR = "promocode_error_menu"
PAGE_OK = "promocode_success_menu"


def _caption(page, fallback: str) -> str:
    if not page:
        return fallback
    title = page.title or ""
    body = page.content or ""
    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    return title or body or fallback


async def _send_page_photo_or_text(message_or_callback, *, page, caption: str, kb):
    image = page.image if page else None
    if image:
        # message_or_callback может быть Message или CallbackQuery.message
        await message_or_callback.answer_photo(photo=image, caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await message_or_callback.answer(caption, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "enter_promocode")
async def enter_promocode_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_PROMO)
    caption = _caption(page, "Введите промокод:")

    if page and page.image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=page.image, caption=caption, parse_mode="HTML"),
            reply_markup=promocode_kb(),
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=promocode_kb())

    await state.set_state(PromocodeStates.waiting_for_code)
    await callback.answer()


@router.message(PromocodeStates.waiting_for_code)
async def process_promocode_msg(
    message: Message,
    state: FSMContext,
    shop_id: int,
    user_repo: ShopUserRepository,
    promocode_repo: ShopPromocodeRepository,
    page_repo: ShopPageRepository,
):
    tg_id = message.from_user.id
    code = (message.text or "").strip()

    if not code:
        page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ERR)
        caption = _caption(page, "❌ Введите промокод текстом")
        await _send_page_photo_or_text(message, page=page, caption=caption, kb=promocode_kb())
        return

    promocode = await promocode_repo.activate_promocode(shop_id=shop_id, code=code, tg_id=tg_id)

    if promocode is None:
        page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_ERR)
        caption = _caption(page, "❌ Промокод недействителен или уже использован")
        await _send_page_photo_or_text(message, page=page, caption=caption, kb=promocode_kb())
        await state.clear()
        return

    await user_repo.increase_balance(shop_id=shop_id, tg_id=tg_id, amount=promocode.amount)

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_OK)
    caption = (
        _caption(page, "✅ Промокод активирован!")
        + f"\n\n🎁 Баланс пополнен на {promocode.amount} RUB."
    )
    await _send_page_photo_or_text(message, page=page, caption=caption, kb=back_promocode_kb())
    await state.clear()
