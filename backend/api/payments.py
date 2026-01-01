from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.database.models import Shop, ShopPaymentConfig

router = APIRouter(tags=["payments"])

Provider = Literal["lava", "pally"]


class PaymentConfigOut(BaseModel):
    id: int
    shop_id: int
    provider: str
    shop_id_value: Optional[str] = None
    secret_key: Optional[str] = None
    api_token: Optional[str] = None

    success_url: str
    fail_url: str

    is_active: bool

    class Config:
        from_attributes = True


class PaymentConfigCreateIn(BaseModel):
    shop_id: int
    provider: Provider
    shop_id_value: Optional[str] = Field(default=None, max_length=128)
    secret_key: Optional[str] = Field(default=None, max_length=255)
    api_token: Optional[str] = Field(default=None, max_length=255)

    success_url: str = Field(default="", max_length=512)
    fail_url: str = Field(default="", max_length=512)

    is_active: bool = True


class PaymentConfigUpdateIn(BaseModel):
    shop_id_value: Optional[str] = Field(default=None, max_length=128)
    secret_key: Optional[str] = Field(default=None, max_length=255)
    api_token: Optional[str] = Field(default=None, max_length=255)

    success_url: Optional[str] = Field(default=None, max_length=512)
    fail_url: Optional[str] = Field(default=None, max_length=512)

    is_active: Optional[bool] = None


async def _ensure_shop(session: AsyncSession, shop_id: int) -> Shop:
    shop = await session.scalar(select(Shop).where(Shop.id == shop_id))
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


async def _ensure_cfg(session: AsyncSession, shop_id: int, cfg_id: int) -> ShopPaymentConfig:
    cfg = await session.scalar(
        select(ShopPaymentConfig).where(
            ShopPaymentConfig.id == cfg_id,
            ShopPaymentConfig.shop_id == shop_id,
        )
    )
    if not cfg:
        raise HTTPException(status_code=404, detail="Payment config not found")
    return cfg


def _validate_provider_fields(
    provider: str,
    shop_id_value: Optional[str],
    secret_key: Optional[str],
    api_token: Optional[str],
):
    if provider == "lava":
        if not shop_id_value or not secret_key:
            raise HTTPException(status_code=400, detail="Lava requires shop_id_value + secret_key")
    if provider == "pally":
        if not api_token:
            raise HTTPException(status_code=400, detail="Pally requires api_token")


@router.get("", response_model=list[PaymentConfigOut])
async def list_payment_configs(
    shop_id: int = Query(...),
    only_active: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, shop_id)

    stmt = select(ShopPaymentConfig).where(ShopPaymentConfig.shop_id == shop_id)
    if only_active:
        stmt = stmt.where(ShopPaymentConfig.is_active.is_(True))

    stmt = stmt.order_by(ShopPaymentConfig.id.asc())
    cfgs = (await session.execute(stmt)).scalars().all()
    return cfgs


@router.get("/by-provider", response_model=PaymentConfigOut)
async def get_payment_config_by_provider(
    shop_id: int = Query(...),
    provider: Provider = Query(...),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, shop_id)

    cfg = await session.scalar(
        select(ShopPaymentConfig).where(
            ShopPaymentConfig.shop_id == shop_id,
            ShopPaymentConfig.provider == provider,
        )
    )
    if not cfg:
        raise HTTPException(status_code=404, detail="Payment config not found")
    return cfg


@router.post("", response_model=PaymentConfigOut)
async def create_payment_config(
    payload: PaymentConfigCreateIn,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    await _ensure_shop(session, payload.shop_id)
    _validate_provider_fields(payload.provider, payload.shop_id_value, payload.secret_key, payload.api_token)

    cfg = ShopPaymentConfig(
        shop_id=payload.shop_id,
        provider=payload.provider,
        shop_id_value=payload.shop_id_value,
        secret_key=payload.secret_key,
        api_token=payload.api_token,

        success_url=(payload.success_url or "").strip(),
        fail_url=(payload.fail_url or "").strip(),

        is_active=payload.is_active,
    )
    session.add(cfg)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Config for this provider already exists for this shop")

    await session.refresh(cfg)
    return cfg


@router.patch("/{cfg_id}", response_model=PaymentConfigOut)
async def update_payment_config(
    cfg_id: int,
    shop_id: int = Query(...),
    payload: PaymentConfigUpdateIn = ...,
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    cfg = await _ensure_cfg(session, shop_id, cfg_id)

    if payload.shop_id_value is not None:
        cfg.shop_id_value = payload.shop_id_value
    if payload.secret_key is not None:
        cfg.secret_key = payload.secret_key
    if payload.api_token is not None:
        cfg.api_token = payload.api_token

    if payload.success_url is not None:
        cfg.success_url = (payload.success_url or "").strip()
    if payload.fail_url is not None:
        cfg.fail_url = (payload.fail_url or "").strip()

    if payload.is_active is not None:
        cfg.is_active = payload.is_active

    _validate_provider_fields(cfg.provider, cfg.shop_id_value, cfg.secret_key, cfg.api_token)

    await session.commit()
    await session.refresh(cfg)
    return cfg


@router.delete("/{cfg_id}")
async def delete_payment_config(
    cfg_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    cfg = await _ensure_cfg(session, shop_id, cfg_id)
    await session.delete(cfg)
    await session.commit()
    return {"ok": True}
