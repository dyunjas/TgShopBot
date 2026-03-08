from __future__ import annotations

from collections import OrderedDict
import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.payment_config_repo import PaymentConfigRepository

PALLY_API_URL_CREATE = "https://pal24.pro/api/v1/bill/create"
PALLY_API_URL_STATUS = "https://pal24.pro/api/v1/bill/status"

_session: aiohttp.ClientSession | None = None


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=20)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def create_invoice_pally(
    session: AsyncSession,
    shop_id: int,
    amount: float,
    order_id: str,
    description: str,
    success_url: str | None = None,
    fail_url: str | None = None,
    ttl: int = 600,
):
    cfg = await PaymentConfigRepository(session).get(shop_id, "pally")
    if not cfg or not cfg.api_token or not cfg.shop_id_value:
        raise RuntimeError(f"PALLY config not set for shop_id={shop_id}")

    # если не передали — возьмём из БД (если поля есть)
    if not success_url:
        success_url = getattr(cfg, "success_url", None) or None
    if not fail_url:
        fail_url = getattr(cfg, "fail_url", None) or None

    data = OrderedDict([
        ("amount", round(float(amount), 2)),
        ("shop_id", cfg.shop_id_value),
        ("order_id", str(order_id)),
        ("description", description),
        ("type", "normal"),
        ("currency_in", "RUB"),
        ("name", "SHOPCHECK"),
        ("ttl", int(ttl)),
    ])

    if success_url:
        data["success_url"] = success_url
    if fail_url:
        data["fail_url"] = fail_url

    headers = {
        "Authorization": f"Bearer {cfg.api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    http = await _get_session()
    async with http.post(PALLY_API_URL_CREATE, json=data, headers=headers) as resp:
        # иногда полезно видеть код, но оставим только json как было
        return await resp.json()


async def get_invoice_status_pally(
    session: AsyncSession,
    shop_id: int,
    bill_id: str,
):
    cfg = await PaymentConfigRepository(session).get(shop_id, "pally")
    if not cfg or not cfg.api_token:
        raise RuntimeError(f"PALLY config not set for shop_id={shop_id}")

    headers = {
        "Authorization": f"Bearer {cfg.api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    http = await _get_session()
    async with http.get(f"{PALLY_API_URL_STATUS}?id={bill_id}", headers=headers) as resp:
        return await resp.json()
