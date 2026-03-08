from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role
from backend.services.admin import PaymentsService

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


def get_service(session: AsyncSession = Depends(get_session)) -> PaymentsService:
    return PaymentsService(session)


@router.get("", response_model=list[PaymentConfigOut])
async def list_payment_configs(
    shop_id: int = Query(...),
    only_active: bool = Query(default=False),
    service: PaymentsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.list_configs(shop_id=shop_id, only_active=only_active)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/by-provider", response_model=PaymentConfigOut)
async def get_payment_config_by_provider(
    shop_id: int = Query(...),
    provider: Provider = Query(...),
    service: PaymentsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.get_by_provider(shop_id=shop_id, provider=provider)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=PaymentConfigOut)
async def create_payment_config(
    payload: PaymentConfigCreateIn,
    session: AsyncSession = Depends(get_session),
    service: PaymentsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        cfg = await service.create_config(
            shop_id=payload.shop_id,
            provider=payload.provider,
            shop_id_value=payload.shop_id_value,
            secret_key=payload.secret_key,
            api_token=payload.api_token,
            success_url=payload.success_url,
            fail_url=payload.fail_url,
            is_active=payload.is_active,
        )
        await session.commit()
        return cfg
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Config for this provider already exists for this shop")


@router.patch("/{cfg_id}", response_model=PaymentConfigOut)
async def update_payment_config(
    cfg_id: int,
    shop_id: int = Query(...),
    payload: PaymentConfigUpdateIn = ...,
    session: AsyncSession = Depends(get_session),
    service: PaymentsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        cfg = await service.update_config(
            cfg_id=cfg_id,
            shop_id=shop_id,
            shop_id_value=payload.shop_id_value,
            secret_key=payload.secret_key,
            api_token=payload.api_token,
            success_url=payload.success_url,
            fail_url=payload.fail_url,
            is_active=payload.is_active,
        )
        await session.commit()
        return cfg
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cfg_id}")
async def delete_payment_config(
    cfg_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: PaymentsService = Depends(get_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        result = await service.delete_config(cfg_id=cfg_id, shop_id=shop_id)
        await session.commit()
        return result
    except LookupError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
