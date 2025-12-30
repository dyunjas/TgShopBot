import json
import hmac
import hashlib
import aiohttp
from ..core.loader import settings
import requests
from collections import OrderedDict
import asyncio 

LAVA_API_URL = "https://api.lava.ru/business/invoice/create"
LAVA_API_URL_STATUS = "https://api.lava.ru/business/invoice/status"

SHOP_ID = settings.LAVA_SHOP_ID
SECRET_KEY = settings.LAVA_SECRET_KEY

session: aiohttp.ClientSession | None = None

async def get_session() -> aiohttp.ClientSession:
    global session
    if session is None or session.closed:
        timeout = aiohttp.ClientTimeout(total=20)
        session = aiohttp.ClientSession(timeout=timeout)
    return session

async def create_invoice_LAVA(amount, order_id, comment, success_url, fail_url, hook_url):
    def create_invoice_sync():
        data = OrderedDict([
            ("comment", comment),
            ("customFields", str(order_id)),
            ("expire", 300),
            ("failUrl", fail_url),
            ("hookUrl", hook_url),
            ("includeService", ["sbp"]),
            ("orderId", order_id),
            ("shopId", SHOP_ID),
            ("successUrl", success_url),
            ("sum", round(float(amount), 2))
        ])
        json_str = json.dumps(data, separators=(",", ":"))
        signature = hmac.new(SECRET_KEY.encode(), json_str.encode(), hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Signature": signature
        }
        resp = requests.post(LAVA_API_URL, data=json_str, headers=headers, timeout=20)
        return resp.json()

    return await asyncio.to_thread(create_invoice_sync)

async def get_invoice_status_LAVA(order_id: str | None = None, invoice_id: str | None = None):
    if order_id is None and invoice_id is None:
        raise ValueError
    
    payload = OrderedDict()
    payload["shopId"] = SHOP_ID
    if order_id:
        payload["orderId"] = str(order_id)
    if invoice_id:
        payload["invoiceId"] = str(invoice_id)

    json_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()

    signature = hmac.new(SECRET_KEY.encode(), json_str, hashlib.sha256).hexdigest()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Signature": signature
    }

    def sync_request():
        return requests.post(LAVA_API_URL_STATUS, data=json_str, headers=headers, timeout=20).json()

    response = await asyncio.to_thread(sync_request)

    return response