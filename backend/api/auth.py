from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from backend.core.config import settings
from backend.database.models import AdminUser, AdminLoginCode
from backend.database.session import async_session
from backend.services.tg_sender import TgSender

from .jwt import create_access_token
from .utils.code_utils import gen_code, hash_code, verify_code


router = APIRouter(tags=["auth"])

CODE_TTL_MIN = 5
CODE_SALT = settings.JWT_SECRET


def utcnow_naive() -> datetime:
    return datetime.now()


def expires_at_naive(minutes: int) -> datetime:
    return utcnow_naive() + timedelta(minutes=minutes)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


class RequestCodeIn(BaseModel):
    tg_id: int


class VerifyCodeIn(BaseModel):
    tg_id: int
    code: str


@router.post("/request-code")
async def request_code(
    payload: RequestCodeIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    tg_id = payload.tg_id

    admin = await session.scalar(select(AdminUser).where(AdminUser.tg_id == tg_id))
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    code = gen_code()
    code_h = hash_code(code, CODE_SALT)

    await session.execute(
        update(AdminLoginCode)
        .where(AdminLoginCode.tg_id == tg_id, AdminLoginCode.used_at.is_(None))
        .values(used_at=utcnow_naive())
    )

    rec = AdminLoginCode(
        tg_id=tg_id,
        code_hash=code_h,
        expires_at=expires_at_naive(CODE_TTL_MIN),
        used_at=None,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        created_at=utcnow_naive(),
    )
    session.add(rec)
    await session.commit()

    sender = TgSender(settings.DROP_BOT_TOKEN)
    try:
        await sender.send_login_code(tg_id, code)
    finally:
        await sender.close()

    return {"ok": True}


@router.post("/verify")
async def verify_code_ep(payload: VerifyCodeIn, session: AsyncSession = Depends(get_session)):
    tg_id = payload.tg_id
    code = payload.code.strip()

    admin = await session.scalar(select(AdminUser).where(AdminUser.tg_id == tg_id))
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid code")

    rec = await session.scalar(
        select(AdminLoginCode)
        .where(AdminLoginCode.tg_id == tg_id, AdminLoginCode.used_at.is_(None))
        .order_by(AdminLoginCode.created_at.desc())
        .limit(1)
    )
    if not rec:
        raise HTTPException(status_code=401, detail="Invalid code")

    if rec.expires_at < utcnow_naive():
        raise HTTPException(status_code=401, detail="Code expired")

    if not verify_code(code, rec.code_hash, CODE_SALT):
        raise HTTPException(status_code=401, detail="Invalid code")

    rec.used_at = utcnow_naive()
    await session.commit()

    token = create_access_token(
        secret=settings.JWT_SECRET,
        admin_id=admin.id,
        role=getattr(admin, "role", "operator"),
        minutes=getattr(settings, "JWT_EXPIRES_MIN", 60),
    )

    return {
        "access_token": token,
        "admin": {
            "id": admin.id,
            "tg_id": admin.tg_id,
            "role": getattr(admin, "role", "operator"),
            "balance": admin.balance,
        },
    }
