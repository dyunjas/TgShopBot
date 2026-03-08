from __future__ import annotations

from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from backend.states import PaymentStates
from backend.payments.generate_pally_invoice import create_invoice_pally, get_invoice_status_pally
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.transaction_repository import ShopTransactionRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from backend.core.logger_config import logger
from bot.utils.media_fallback import safe_answer_photo_or_text, safe_edit_photo_or_text

from .keyboards import back_profile_kb, payment_menu_kb

router = Router()

PAGE_PALLY = "pally_payment_menu"
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


def _is_success_flag(v) -> bool:
    # Pally может вернуть success: true/false, 1/0, "true"/"false"
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return int(v) == 1
    s = str(v or "").strip().lower()
    return s in ("true", "1", "yes", "ok", "success")


def _pick(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


@router.callback_query(F.data == "pay_pally", PaymentStates.waiting_for_payment_system)
async def pay_pally_clb(
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

    logger.info(f"[PALLY] create invoice shop_id={shop_id} tg_id={tg_id} amount={amount} data={data}")

    order_id = f"TPU-{shop_id}-{tg_id}-{int(datetime.now().timestamp())}"

    # ВАЖНО: create_invoice_pally сам возьмёт success_url/fail_url из конфига (см. ниже)
    invoice = await create_invoice_pally(
        session=transaction_repo.session,
        shop_id=shop_id,
        amount=float(amount),
        order_id=order_id,
        description=f"Пополнение баланса на {amount} RUB",
    )

    # иногда полезные поля лежат в invoice["data"]
    invoice_data = invoice.get("data") if isinstance(invoice.get("data"), dict) else {}
    ok = _is_success_flag(invoice.get("success")) or _is_success_flag(invoice_data.get("success"))

    if not ok:
        await callback.answer("❌ Ошибка создания счёта", show_alert=True)
        logger.error(f"[PALLY] invoice create error payload={invoice}")
        return

    invoice_url = _pick(invoice_data, "link_page_url", "pay_url", "url", "link") or _pick(
        invoice, "link_page_url", "pay_url", "url", "link"
    )
    invoice_id = _pick(invoice_data, "bill_id", "id", "invoice_id") or _pick(invoice, "bill_id", "id", "invoice_id")

    if not invoice_url or not invoice_id:
        await callback.answer("❌ Не удалось получить ссылку/ID счёта", show_alert=True)
        logger.error(f"[PALLY] bad invoice payload: {invoice}")
        return

    await transaction_repo.create_transaction(
        shop_id=shop_id,
        tg_id=tg_id,
        transaction_id=str(invoice_id),
        amount=int(amount),
        payment_system="PALLY",
        order_id=order_id,
    )

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_PALLY)
    fallback = (
        "💳 Счёт создан, перейдите по ссылке для оплаты!\n"
        f"<pre><code>ID транзакции: {invoice_id}</code></pre>\n"
    )
    text = _caption(page, fallback)
    image = page.image if page else None

    kb = payment_menu_kb(
        invoice_url=str(invoice_url),
        invoice_id=str(invoice_id),
        check_prefix="check_payment_pally",
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
        logger.warning(f"[PALLY] safe edit failed, sending new: {e}")
        await safe_answer_photo_or_text(
            message=callback.message,
            image=image,
            text=text,
            parse_mode="HTML",
            reply_markup=kb,
        )

    await state.update_data(order_id=order_id, invoice_id=str(invoice_id), provider="pally")
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_pally:"))
async def check_pally_payment_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    user_repo: ShopUserRepository,
    transaction_repo: ShopTransactionRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    invoice_id = callback.data.split(":", 1)[1]

    tx = await transaction_repo.get_transaction_by_payment_system_id(
        shop_id=shop_id, transaction_id=str(invoice_id)
    )
    if not tx:
        await callback.answer("Транзакция не найдена.", show_alert=True)
        return

    status_data = await get_invoice_status_pally(
        session=transaction_repo.session,
        shop_id=shop_id,
        bill_id=str(invoice_id),
    )

    status_inner = status_data.get("data") if isinstance(status_data.get("data"), dict) else {}
    ok = _is_success_flag(status_data.get("success")) or _is_success_flag(status_inner.get("success"))
    if not ok:
        await callback.answer("Ошибка запроса статуса", show_alert=True)
        logger.error(f"[PALLY] status error payload={status_data}")
        return

    invoice_status = _pick(status_inner, "status", "state") or _pick(status_data, "status", "state")
    invoice_status = str(invoice_status or "").upper()

    if invoice_status == "SUCCESS":
        if getattr(tx, "paid", False):
            await callback.answer("✅ Платёж уже подтверждён.", show_alert=True)
            return

        await user_repo.increase_balance(shop_id=shop_id, tg_id=tg_id, amount=tx.amount)
        await transaction_repo.mark_transaction_as_paid(shop_id=shop_id, transaction_id=str(invoice_id))

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
            logger.warning(f"[PALLY] success safe edit failed, sending new: {e}")
            await safe_answer_photo_or_text(
                message=callback.message,
                image=image,
                text=text,
                parse_mode="HTML",
                reply_markup=back_profile_kb(),
            )

        logger.info(f"[PALLY] Payment OK shop_id={shop_id} tg_id={tg_id} invoice_id={invoice_id} amount={tx.amount}")
        await state.clear()
        await callback.answer()
        return

    status_map = {
        "NEW": "новый (ожидает оплаты)",
        "PROCESS": "в обработке",
        "UNDERPAID": "оплачен не полностью",
        "OVERPAID": "оплачен больше суммы",
        "FAIL": "неуспешный",
        "CANCEL": "отменён",
        "EXPIRED": "просрочен",
    }
    human_status = status_map.get(invoice_status, invoice_status or "UNKNOWN")

    await callback.answer(
        text=f"⚠️ Оплата не завершена. Статус: {human_status}. Попробуйте ещё раз через несколько минут.",
        show_alert=True,
    )
