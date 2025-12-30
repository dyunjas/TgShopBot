from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.images.images_url import TOPUP_BALANCE_MENU_URL, SUCCESS_PAYMENT_MENU
from .keyboards import back_profile_kb, payment_menu_kb
from backend.states import PaymentStates

from backend.payments.generate_lava_invoice import create_invoice_LAVA, get_invoice_status_LAVA

from datetime import datetime

from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.transaction_repository import ShopTransactionRepository

from backend.core.logger_config import logger

router = Router()

@router.callback_query(F.data == "pay_lava", PaymentStates.waiting_for_payment_system)
async def pay_lava_clb(
    callback: CallbackQuery,
    state: FSMContext,
    transaction_repo: ShopTransactionRepository,
):
    tg_id = callback.from_user.id
    data = await state.get_data()
    amount = int(data.get("amount"))
    logger.info(f"[LAVA] Received data: {tg_id} {data}")

    order_id = f"TPU-{tg_id}-{int(datetime.now().timestamp())}"

    invoice = await create_invoice_LAVA(
        amount=amount,
        order_id=order_id,
        comment=f"Пополнение баланса на {amount} RUB",
        success_url="https://t.me/shopchek_bot",
        fail_url="https://t.me/shopchek_bot",
        hook_url=""
    )

    if invoice.get("status") == 200:
        invoice_url = invoice["data"]["url"]
        invoice_id = invoice["data"]["id"]

        try:
            await transaction_repo.create_transaction(
                tg_id=tg_id,
                transaction_id=invoice_id,
                amount=int(amount),
                payment_system="LAVA",
                order_id=order_id,
            )
        except Exception as e:
            logger.exception(f"Error creating transaction: {e}")
            pass

        text = (
            "💳 Cчёт создан, перейдите по ссылке для оплаты!\n"
            f"<pre><code>ID транзакции: {invoice_id}</code></pre>\n"
        )
        content = InputMediaPhoto(
            media=TOPUP_BALANCE_MENU_URL,
            caption=text,
            parse_mode="HTML"
        )
        await callback.message.edit_media(
            media=content,
            reply_markup=payment_menu_kb(invoice_url=invoice_url, invoice_id=invoice_id)
        )
        await state.update_data(order_id=order_id, invoice_id=invoice_id)
        await callback.answer()
    else:
        await callback.answer(f"❌ Ошибка создания счёта: {invoice.get('error')}", show_alert=True)
        logger.error(f"LAVA invoice creation error: {invoice.get('error')}")


@router.callback_query(F.data.startswith("check_payment:"))
async def check_lava_payment_clb(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: ShopUserRepository,
    transaction_repo: ShopTransactionRepository
):
    tg_id = callback.from_user.id
    invoice_id = callback.data.split(":")[1]

    transaction = await transaction_repo.get_transaction_by_payment_system_id(invoice_id)
    if not transaction or transaction.user.tg_id is None:
        await callback.answer(text="Транзакция не найдена.", show_alert=True)
        return

    status_data = await get_invoice_status_LAVA(invoice_id=invoice_id)
    if status_data.get("status") != 200:
        await callback.answer(text=f"Ошибка запроса: {status_data.get('error')}", show_alert=True)
        logger.error(f"LAVA invoice status error: {status_data.get('error')}")
        return

    invoice = status_data["data"]
    inv_status = invoice.get("status")

    if inv_status == "success":
        if getattr(transaction, "paid", False):
            await callback.answer(text="✅ Платёж уже подтверждён.", show_alert=True)
            return

        await user_repo.increase_balance(tg_id, transaction.amount)

        await transaction_repo.mark_transaction_as_paid(invoice_id)

        text = f"✅ Оплата успешно завершена! \n\nБаланс пополнен на {transaction.amount} RUB"
        content = InputMediaPhoto(media=SUCCESS_PAYMENT_MENU, caption=text)
        await callback.message.edit_media(media=content, reply_markup=back_profile_kb())
        logger.info(f"Payment successful for tg_id={tg_id}, invoice_id={invoice_id}, amount={transaction.amount}")
        await state.clear()
        await callback.answer()
    else:
        human = "ожидает оплаты" if inv_status == "created" else inv_status
        await callback.answer(
            text=f"⚠️ Оплата не завершена. Статус: {human}. Попробуйте ещё раз через несколько минут.",
            show_alert=True
        )
