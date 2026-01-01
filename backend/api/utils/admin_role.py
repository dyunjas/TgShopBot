from __future__ import annotations

from typing import Literal, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.database.models import AdminUser
from backend.database.session import async_session

bearer = HTTPBearer(auto_error=False)


async def get_session():
    async with async_session() as s:
        yield s


class CurrentAdmin:
    def __init__(self, admin: AdminUser):
        self.admin = admin

    @property
    def id(self) -> int:
        return self.admin.id

    @property
    def tg_id(self) -> int:
        return self.admin.tg_id

    @property
    def role(self) -> str:
        return getattr(self.admin, "role", "operator")


async def get_current_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> CurrentAdmin:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = creds.credentials

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        admin_id = int(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    admin = await session.scalar(select(AdminUser).where(AdminUser.id == admin_id))
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    return CurrentAdmin(admin)


def require_role(*roles: Literal["operator", "superadmin"]):
    async def _dep(current: CurrentAdmin = Depends(get_current_admin)) -> CurrentAdmin:
        if current.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current

    return _dep
