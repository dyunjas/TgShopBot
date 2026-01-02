from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import PaymentStates
from backend.core.logger_config import logger
from backend.repositories.shop_page_repository import ShopPageRepository
from backend.repositories.shop_repository import ShopRepository

from .keyboards import back_profile_kb, payment_choice_kb

router = Router()

PAGE_TOPUP = "topup_balance_menu"
PAGE_CHOOSE = "choose_payment_menu"


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


def _has_provider_config(shop, provider: str) -> bool:
    
    if not shop:
        return False

    for c in (getattr(shop, "payment_configs", None) or []):
        prov = (getattr(c, "provider", "") or "").strip().lower()
        if prov != provider.lower():
            continue

        if hasattr(c, "is_active") and getattr(c, "is_active") is False:
            continue

        return True

    return False


@router.callback_query(F.data == "topup_balance")
async def topup_balance_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    page_repo: ShopPageRepository,
):
    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_TOPUP)
    text = _caption(page, "Введите сумму пополнения (RUB):")
    image = page.image if page else None

    try:
        if image:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image, caption=text, parse_mode="HTML"),
                reply_markup=back_profile_kb(),
            )
        else:
            try:
                await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=back_profile_kb())
            except Exception:
                await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=back_profile_kb())
    except Exception as e:
        logger.warning(f"topup_balance_clb: edit failed, sending new: {e}")
        if image:
            await callback.message.answer_photo(photo=image, caption=text, parse_mode="HTML", reply_markup=back_profile_kb())
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=back_profile_kb())

    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()


@router.message(PaymentStates.waiting_for_amount)
async def choose_payment_system_msg(
    message: Message,
    state: FSMContext,
    shop_id: int,
    page_repo: ShopPageRepository,
    shop_repo: ShopRepository,
):
    page_topup = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_TOPUP)
    topup_text_invalid = _caption(page_topup, "Введите целое положительное число (больше 0)")
    topup_image = page_topup.image if page_topup else None

    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        if topup_image:
            await message.answer_photo(
                photo=topup_image,
                caption=topup_text_invalid,
                parse_mode="HTML",
                reply_markup=back_profile_kb(),
            )
        else:
            await message.answer(topup_text_invalid, parse_mode="HTML", reply_markup=back_profile_kb())
        return

    await state.update_data(amount=amount)

    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
    show_pally = _has_provider_config(shop, "PALLY")
    show_lava = _has_provider_config(shop, "LAVA")

    if not show_pally and not show_lava:
        page_choose = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_CHOOSE)
        text = _caption(page_choose, "❌ Сейчас нет доступных способов оплаты. Напишите в поддержку.")
        image = page_choose.image if page_choose else None

        if image:
            await message.answer_photo(photo=image, caption=text, parse_mode="HTML", reply_markup=back_profile_kb())
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=back_profile_kb())

        await state.clear()
        return

    page_choose = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_CHOOSE)
    choose_text = _caption(page_choose, "Выберите платёжную систему:")
    choose_image = page_choose.image if page_choose else None

    kb = payment_choice_kb(show_pally=show_pally, show_lava=show_lava)

    if choose_image:
        await message.answer_photo(photo=choose_image, caption=choose_text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(choose_text, parse_mode="HTML", reply_markup=kb)

    await state.set_state(PaymentStates.waiting_for_payment_system)
