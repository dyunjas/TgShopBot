from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Shop, ShopPaymentConfig


@dataclass
class PaymentsService:
    session: AsyncSession

    async def ensure_shop(self, shop_id: int) -> None:
        shop = await self.session.scalar(select(Shop).where(Shop.id == shop_id))
        if not shop:
            raise LookupError("Shop not found")

    async def ensure_cfg(self, *, shop_id: int, cfg_id: int) -> ShopPaymentConfig:
        cfg = await self.session.scalar(
            select(ShopPaymentConfig).where(
                ShopPaymentConfig.id == cfg_id,
                ShopPaymentConfig.shop_id == shop_id,
            )
        )
        if not cfg:
            raise LookupError("Payment config not found")
        return cfg

    @staticmethod
    def validate_provider_fields(
        provider: str,
        shop_id_value: Optional[str],
        secret_key: Optional[str],
        api_token: Optional[str],
    ) -> None:
        if provider == "lava":
            if not shop_id_value or not secret_key:
                raise ValueError("Lava requires shop_id_value + secret_key")
        if provider == "pally":
            if not shop_id_value or not api_token:
                raise ValueError("Pally requires shop_id_value + api_token")

    async def list_configs(self, *, shop_id: int, only_active: bool) -> list[ShopPaymentConfig]:
        await self.ensure_shop(shop_id)
        stmt = select(ShopPaymentConfig).where(ShopPaymentConfig.shop_id == shop_id)
        if only_active:
            stmt = stmt.where(ShopPaymentConfig.is_active.is_(True))
        stmt = stmt.order_by(ShopPaymentConfig.id.asc())
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_provider(self, *, shop_id: int, provider: str) -> ShopPaymentConfig:
        await self.ensure_shop(shop_id)
        cfg = await self.session.scalar(
            select(ShopPaymentConfig).where(
                ShopPaymentConfig.shop_id == shop_id,
                ShopPaymentConfig.provider == provider,
            )
        )
        if not cfg:
            raise LookupError("Payment config not found")
        return cfg

    async def create_config(
        self,
        *,
        shop_id: int,
        provider: str,
        shop_id_value: str | None,
        secret_key: str | None,
        api_token: str | None,
        success_url: str,
        fail_url: str,
        is_active: bool,
    ) -> ShopPaymentConfig:
        await self.ensure_shop(shop_id)
        self.validate_provider_fields(provider, shop_id_value, secret_key, api_token)

        cfg = ShopPaymentConfig(
            shop_id=shop_id,
            provider=provider,
            shop_id_value=shop_id_value,
            secret_key=secret_key,
            api_token=api_token,
            success_url=(success_url or "").strip(),
            fail_url=(fail_url or "").strip(),
            is_active=is_active,
        )
        self.session.add(cfg)
        await self.session.flush()
        await self.session.refresh(cfg)
        return cfg

    async def update_config(
        self,
        *,
        cfg_id: int,
        shop_id: int,
        shop_id_value: str | None = None,
        secret_key: str | None = None,
        api_token: str | None = None,
        success_url: str | None = None,
        fail_url: str | None = None,
        is_active: bool | None = None,
    ) -> ShopPaymentConfig:
        cfg = await self.ensure_cfg(shop_id=shop_id, cfg_id=cfg_id)

        if shop_id_value is not None:
            cfg.shop_id_value = shop_id_value
        if secret_key is not None:
            cfg.secret_key = secret_key
        if api_token is not None:
            cfg.api_token = api_token
        if success_url is not None:
            cfg.success_url = (success_url or "").strip()
        if fail_url is not None:
            cfg.fail_url = (fail_url or "").strip()
        if is_active is not None:
            cfg.is_active = is_active

        self.validate_provider_fields(cfg.provider, cfg.shop_id_value, cfg.secret_key, cfg.api_token)
        await self.session.flush()
        await self.session.refresh(cfg)
        return cfg

    async def delete_config(self, *, cfg_id: int, shop_id: int) -> dict:
        cfg = await self.ensure_cfg(shop_id=shop_id, cfg_id=cfg_id)
        await self.session.delete(cfg)
        await self.session.flush()
        return {"ok": True}
