import json
import hmac
import hashlib
import asyncio
from collections import OrderedDict
import requests

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.payment_config_repo import PaymentConfigRepository


LAVA_API_URL = "https://api.lava.ru/business/invoice/create"
LAVA_API_URL_STATUS = "https://api.lava.ru/business/invoice/status"


async def create_invoice_lava(
    session: AsyncSession,
    shop_id: int,
    amount: float,
    order_id: str,
    comment: str,
    success_url: str,
    fail_url: str,
    hook_url: str,
):

    cfg = await PaymentConfigRepository(session).get(shop_id, "lava")
    if not cfg or not cfg.shop_id_value or not cfg.secret_key:
        raise RuntimeError(f"LAVA config not set for shop_id={shop_id}")

    def _sync():
        data = OrderedDict([
            ("comment", comment),
            ("customFields", str(order_id)),
            ("expire", 300),
            ("failUrl", fail_url),
            ("hookUrl", hook_url),
            ("includeService", ["sbp"]),
            ("orderId", order_id),
            ("shopId", cfg.shop_id_value),
            ("successUrl", success_url),
            ("sum", round(float(amount), 2)),
        ])

        json_str = json.dumps(data, separators=(",", ":"))
        signature = hmac.new(
            cfg.secret_key.encode(),
            json_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Signature": signature,
        }

        resp = requests.post(
            LAVA_API_URL,
            data=json_str,
            headers=headers,
            timeout=20,
        )
        return resp.json()

    return await asyncio.to_thread(_sync)


async def get_invoice_status_lava(
    session: AsyncSession,
    shop_id: int,
    order_id: str | None = None,
    invoice_id: str | None = None,
):
    if not order_id and not invoice_id:
        raise ValueError("order_id or invoice_id required")

    cfg = await PaymentConfigRepository(session).get(shop_id, "lava")
    if not cfg or not cfg.shop_id_value or not cfg.secret_key:
        raise RuntimeError(f"LAVA config not set for shop_id={shop_id}")

    payload = OrderedDict()
    payload["shopId"] = cfg.shop_id_value
    if order_id:
        payload["orderId"] = str(order_id)
    if invoice_id:
        payload["invoiceId"] = str(invoice_id)

    json_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()

    signature = hmac.new(
        cfg.secret_key.encode(),
        json_bytes,
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Signature": signature,
    }

    def _sync():
        return requests.post(
            LAVA_API_URL_STATUS,
            data=json_bytes,
            headers=headers,
            timeout=20,
        ).json()

    return await asyncio.to_thread(_sync)
