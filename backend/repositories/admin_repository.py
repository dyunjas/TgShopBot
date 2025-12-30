from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import AdminUser


class AdminUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tg_id(self, tg_id: int) -> AdminUser | None:
        res = await self.session.execute(select(AdminUser).where(AdminUser.tg_id == tg_id))
        return res.scalar_one_or_none()

    async def create_admin(self, tg_id: int, username: str | None) -> AdminUser:
        admin = AdminUser(tg_id=tg_id, username=username, balance=0)
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin

    async def ensure_admin(self, tg_id: int, username: str | None) -> AdminUser:
        admin = await self.get_by_tg_id(tg_id)
        if admin:
            if username and admin.username != username:
                admin.username = username
                await self.session.commit()
                await self.session.refresh(admin)
            return admin
        return await self.create_admin(tg_id, username)

    async def increase_balance(self, tg_id: int, amount: int) -> int:
        stmt = (
            select(AdminUser)
            .where(AdminUser.tg_id == tg_id)
            .with_for_update()
        )
        res = await self.session.execute(stmt)
        admin = res.scalar_one()
        admin.balance += amount
        await self.session.commit()
        await self.session.refresh(admin)
        return admin.balance
