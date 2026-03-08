from __future__ import annotations

from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from backend.states import PaymentStates
from backend.payments.generate_lava_invoice import create_invoice_lava, get_invoice_status_lava
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.transaction_repository import ShopTransactionRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from backend.core.logger_config import logger
from bot.utils.media_fallback import safe_answer_photo_or_text, safe_edit_photo_or_text

from .keyboards import back_profile_kb, payment_menu_kb

router = Router()

PAGE_LAVA = "lava_payment_menu"
PAGE_SUCCESS = "success_payment_menu"


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


@router.callback_query(F.data == "pay_lava", PaymentStates.waiting_for_payment_system)
async def pay_lava_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    transaction_repo: ShopTransactionRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    data = await state.get_data()
    amount = int(data.get("amount") or 0)

    if amount <= 0:
        return await callback.answer("Сумма не найдена, начните заново", show_alert=True)

    success_url = "https://google.com"
    fail_url = "https://google.com"

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

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_LAVA)
    fallback = (
        "💳 Счёт создан, перейдите по ссылке для оплаты!\n"
        f"<pre><code>ID транзакции: {invoice_id}</code></pre>\n"
    )
    text = _caption(page, fallback)
    image = page.image if page else None

    kb = payment_menu_kb(
        invoice_url=invoice_url,
        invoice_id=str(invoice_id),
        check_prefix="check_payment_lava",
    )
    try:
        await safe_edit_photo_or_text(
            message=callback.message,
            image=image,
            text=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"[LAVA] safe edit failed, sending new: {e}")
        await safe_answer_photo_or_text(
            message=callback.message,
            image=image,
            text=text,
            parse_mode="HTML",
            reply_markup=kb,
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
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    invoice_id = callback.data.split(":", 1)[1]

    tx = await transaction_repo.get_transaction_by_payment_system_id(shop_id=shop_id, transaction_id=invoice_id)
    if not tx:
        await callback.answer("Транзакция не найдена.", show_alert=True)
        return

    status_data = await get_invoice_status_lava(session=transaction_repo.session, shop_id=shop_id, invoice_id=invoice_id)
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

        page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_SUCCESS)
        fallback = f"✅ Оплата успешно завершена!\n\nБаланс пополнен на {tx.amount} RUB"
        text = _caption(page, fallback)
        image = page.image if page else None

        try:
            await safe_edit_photo_or_text(
                message=callback.message,
                image=image,
                text=text,
                parse_mode="HTML",
                reply_markup=back_profile_kb(),
            )
        except Exception as e:
            logger.warning(f"[LAVA] success safe edit failed, sending new: {e}")
            await safe_answer_photo_or_text(
                message=callback.message,
                image=image,
                text=text,
                parse_mode="HTML",
                reply_markup=back_profile_kb(),
            )

        logger.info(f"[LAVA] Payment OK shop_id={shop_id} tg_id={tg_id} invoice_id={invoice_id} amount={tx.amount}")

        await state.clear()
        await callback.answer()
        return

    human = "ожидает оплаты" if inv_status == "created" else str(inv_status)
    await callback.answer(
        text=f"⚠️ Оплата не завершена. Статус: {human}. Попробуйте ещё раз через несколько минут.",
        show_alert=True,
    )
