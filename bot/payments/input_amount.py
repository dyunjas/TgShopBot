from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import PaymentStates
from backend.core.logger_config import logger
from backend.repositories.shop_repository import ShopRepository

from .keyboards import back_profile_kb, payment_choice_kb

router = Router()


async def _get_ui_assets(shop_repo: ShopRepository, shop_id: int) -> tuple[str, str]:
    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)
    ui = getattr(shop, "ui_assets", None) if shop else None

    topup = getattr(ui, "img_topup_menu", "") if ui else ""
    choose = getattr(ui, "img_choose_payment_menu", "") if ui else ""

    return topup.strip(), choose.strip()


@router.callback_query(F.data == "topup_balance")
async def topup_balance_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    shop_repo: ShopRepository,
):
    topup_img, _ = await _get_ui_assets(shop_repo, shop_id)

    text = "Введите сумму пополнения (RUB):"

    try:
        if topup_img:
            content = InputMediaPhoto(media=topup_img, caption=text)
            await callback.message.edit_media(media=content, reply_markup=back_profile_kb())
        else:
            await callback.message.edit_caption(caption=text, reply_markup=back_profile_kb())
    except Exception as e:
        logger.warning(f"topup_balance_clb: edit failed, sending new: {e}")
        if topup_img:
            await callback.message.answer_photo(photo=topup_img, caption=text, reply_markup=back_profile_kb())
        else:
            await callback.message.answer(text, reply_markup=back_profile_kb())

    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()


@router.message(PaymentStates.waiting_for_amount)
async def choose_payment_system_msg(
    message: Message,
    state: FSMContext,
    shop_id: int,
    shop_repo: ShopRepository,
):
    topup_img, choose_img = await _get_ui_assets(shop_repo, shop_id)

    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        text = "Введите целое положительное число (больше 0)"
        if topup_img:
            await message.answer_photo(photo=topup_img, caption=text, reply_markup=back_profile_kb())
        else:
            await message.answer(text, reply_markup=back_profile_kb())
        return

    await state.update_data(amount=amount)

    text = "Выберите платёжную систему:"
    if choose_img:
        await message.answer_photo(photo=choose_img, caption=text, reply_markup=payment_choice_kb())
    else:
        await message.answer(text, reply_markup=payment_choice_kb())

    await state.set_state(PaymentStates.waiting_for_payment_system)
