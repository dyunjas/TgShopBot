from __future__ import annotations

from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.states import PaymentStates
from backend.payments.generate_lava_invoice import create_invoice_lava, get_invoice_status_lava
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.transaction_repository import ShopTransactionRepository
from backend.repositories.shop_repository import ShopRepository
from backend.core.logger_config import logger

from .keyboards import back_profile_kb, payment_menu_kb

router = Router()


async def _get_payment_ui_and_urls(
    shop_repo: ShopRepository,
    shop_id: int,
    provider: str = "LAVA",
) -> tuple[str, str, str, str]:

    shop = await shop_repo.get_shop_by_id(shop_id=shop_id)

    ui = getattr(shop, "ui_assets", None) if shop else None
    img_topup = (getattr(ui, "img_topup_menu", "") if ui else "").strip()
    img_success = (getattr(ui, "img_success_payment_menu", "") if ui else "").strip()

    success_url = ""
    fail_url = ""
    try:
        cfg = None
        for c in (getattr(shop, "payment_configs", None) or []):
            if (getattr(c, "provider", "") or "").lower() == provider.lower():
                cfg = c
                break
        if cfg:
            success_url = (getattr(cfg, "success_url", "") or "").strip()
            fail_url = (getattr(cfg, "fail_url", "") or "").strip()
    except Exception:
        pass

    return img_topup, img_success, success_url, fail_url


@router.callback_query(F.data == "pay_lava", PaymentStates.waiting_for_payment_system)
async def pay_lava_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    transaction_repo: ShopTransactionRepository,
    shop_repo: ShopRepository,
):
    tg_id = callback.from_user.id
    data = await state.get_data()
    amount = int(data.get("amount") or 0)

    if amount <= 0:
        return await callback.answer("Сумма не найдена, начните заново", show_alert=True)

    img_topup, _, success_url, fail_url = await _get_payment_ui_and_urls(
        shop_repo=shop_repo,
        shop_id=shop_id,
        provider="LAVA",
    )

    success_url = success_url or "https://google.com"
    fail_url = fail_url or "https://google.com"

    logger.info(f"[LAVA] shop_id={shop_id} tg_id={tg_id} amount={amount} data={data}")

    order_id = f"TPU-{shop_id}-{tg_id}-{int(datetime.now().timestamp())}"

    invoice = await create_invoice_lava(
        session=transaction_repo.session,
        shop_id=shop_id,
        amount=amount,
        order_id=order_id,
        comment=f"Пополнение баланса на {amount} RUB",
        success_url=success_url,
        fail_url=fail_url,
        hook_url="",
    )

    if invoice.get("status") != 200:
        await callback.answer(f"❌ Ошибка создания счёта: {invoice.get('error')}", show_alert=True)
        logger.error(f"[LAVA] invoice create error: {invoice}")
        return

    inv_data = invoice.get("data") or {}
    invoice_url = inv_data.get("url")
    invoice_id = inv_data.get("id")

    if not invoice_url or not invoice_id:
        await callback.answer("❌ Не удалось получить ссылку/ID счёта", show_alert=True)
        logger.error(f"[LAVA] bad invoice payload: {invoice}")
        return

    await transaction_repo.create_transaction(
        shop_id=shop_id,
        tg_id=tg_id,
        transaction_id=str(invoice_id),
        amount=int(amount),
        payment_system="LAVA",
        order_id=order_id,
    )

    text = (
        "💳 Счёт создан, перейдите по ссылке для оплаты!\n"
        f"<pre><code>ID транзакции: {invoice_id}</code></pre>\n"
    )

    try:
        if img_topup:
            content = InputMediaPhoto(media=img_topup, caption=text, parse_mode="HTML")
            await callback.message.edit_media(
                media=content,
                reply_markup=payment_menu_kb(
                    invoice_url=invoice_url,
                    invoice_id=str(invoice_id),
                    check_prefix="check_payment_lava",
                ),
            )
        else:
            await callback.message.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=payment_menu_kb(
                    invoice_url=invoice_url,
                    invoice_id=str(invoice_id),
                    check_prefix="check_payment_lava",
                ),
            )
    except Exception as e:
        logger.warning(f"[LAVA] edit message failed, sending new: {e}")
        if img_topup:
            await callback.message.answer_photo(
                photo=img_topup,
                caption=text,
                parse_mode="HTML",
                reply_markup=payment_menu_kb(
                    invoice_url=invoice_url,
                    invoice_id=str(invoice_id),
                    check_prefix="check_payment_lava",
                ),
            )
        else:
            await callback.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=payment_menu_kb(
                    invoice_url=invoice_url,
                    invoice_id=str(invoice_id),
                    check_prefix="check_payment_lava",
                ),
            )

    await state.update_data(order_id=order_id, invoice_id=str(invoice_id), provider="lava")
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_lava:"))
async def check_lava_payment_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    user_repo: ShopUserRepository,
    transaction_repo: ShopTransactionRepository,
    shop_repo: ShopRepository,
):
    tg_id = callback.from_user.id
    invoice_id = callback.data.split(":", 1)[1]

    tx = await transaction_repo.get_transaction_by_payment_system_id(
        shop_id=shop_id,
        transaction_id=invoice_id,
    )
    if not tx:
        await callback.answer("Транзакция не найдена.", show_alert=True)
        return

    status_data = await get_invoice_status_lava(
        session=transaction_repo.session,
        shop_id=shop_id,
        invoice_id=invoice_id,
    )
    if status_data.get("status") != 200:
        await callback.answer(text=f"Ошибка запроса: {status_data.get('error')}", show_alert=True)
        logger.error(f"[LAVA] status error: {status_data}")
        return

    inv = status_data.get("data") or {}
    inv_status = inv.get("status")

    if inv_status == "success":
        if getattr(tx, "paid", False):
            await callback.answer("✅ Платёж уже подтверждён.", show_alert=True)
            return

        await user_repo.increase_balance(shop_id=shop_id, tg_id=tg_id, amount=tx.amount)
        await transaction_repo.mark_transaction_as_paid(shop_id=shop_id, transaction_id=invoice_id)

        _, img_success, _, _ = await _get_payment_ui_and_urls(
            shop_repo=shop_repo,
            shop_id=shop_id,
            provider="LAVA",
        )

        text = f"✅ Оплата успешно завершена!\n\nБаланс пополнен на {tx.amount} RUB"

        try:
            if img_success:
                content = InputMediaPhoto(media=img_success, caption=text)
                await callback.message.edit_media(media=content, reply_markup=back_profile_kb())
            else:
                await callback.message.edit_caption(caption=text, reply_markup=back_profile_kb())
        except Exception as e:
            logger.warning(f"[LAVA] success edit failed, sending new: {e}")
            if img_success:
                await callback.message.answer_photo(photo=img_success, caption=text, reply_markup=back_profile_kb())
            else:
                await callback.message.answer(text, reply_markup=back_profile_kb())

        logger.info(f"[LAVA] Payment OK shop_id={shop_id} tg_id={tg_id} invoice_id={invoice_id} amount={tx.amount}")

        await state.clear()
        await callback.answer()
        return

    human = "ожидает оплаты" if inv_status == "created" else str(inv_status)
    await callback.answer(
        text=f"⚠️ Оплата не завершена. Статус: {human}. Попробуйте ещё раз через несколько минут.",
        show_alert=True,
    )
