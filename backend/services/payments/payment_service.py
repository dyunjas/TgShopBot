from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.payment_config_repo import PaymentConfigRepository


Provider = Literal["lava", "pally"]


@dataclass(frozen=True)
class PaymentSecrets:
    provider: Provider
    shop_id_value: Optional[str] = None
    secret_key: Optional[str] = None
    api_token: Optional[str] = None


class PaymentService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cfg_repo = PaymentConfigRepository(session)

    async def get_secrets(self, shop_id: int, provider: Provider) -> PaymentSecrets:
        cfg = await self.cfg_repo.get(shop_id=shop_id, provider=provider)
        if not cfg:
            raise RuntimeError(
                f"Payment config not found: provider='{provider}', shop_id={shop_id}"
            )

        return PaymentSecrets(
            provider=provider,
            shop_id_value=cfg.shop_id_value,
            secret_key=cfg.secret_key,
            api_token=cfg.api_token,
        )

    async def get_lava(self, shop_id: int) -> PaymentSecrets:
        s = await self.get_secrets(shop_id, "lava")
        if not s.shop_id_value or not s.secret_key:
            raise RuntimeError(
                f"LAVA config incomplete for shop_id={shop_id} (need shop_id_value + secret_key)"
            )
        return s

    async def get_pally(self, shop_id: int) -> PaymentSecrets:
        s = await self.get_secrets(shop_id, "pally")
        if not s.shop_id_value or not s.api_token:
            raise RuntimeError(
                f"PALLY config incomplete for shop_id={shop_id} (need shop_id_value + api_token)"
            )
        return s
