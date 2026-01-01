from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import ShopTransaction, ShopUser


class ShopTransactionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction(
        self,
        *,
        shop_id: int,
        tg_id: int,
        transaction_id: str,
        amount: int,
        payment_system: str,
        order_id: str,
        created_at: datetime | None = None,
    ) -> ShopTransaction:
        stmt = select(ShopUser.id).where(
            ShopUser.shop_id == shop_id,
            ShopUser.tg_id == tg_id,
        )
        user_id = (await self.session.execute(stmt)).scalar_one_or_none()
        if user_id is None:
            raise ValueError(f"User with tg_id={tg_id} not found in shop_id={shop_id}")

        tx = ShopTransaction(
            shop_id=shop_id,
            transaction_id=transaction_id,
            amount=amount,
            payment_system=payment_system,
            user_id=user_id,
            order_id=str(order_id),
            created_at=created_at or datetime.now(),
            paid=False,
        )
        self.session.add(tx)
        await self.session.flush()
        await self.session.refresh(tx)
        return tx

    async def get_transactions(self, *, shop_id: int, tg_id: int) -> list[ShopTransaction]:
        stmt = (
            select(ShopTransaction)
            .join(ShopUser, ShopUser.id == ShopTransaction.user_id)
            .where(
                ShopTransaction.shop_id == shop_id,
                ShopUser.shop_id == shop_id,
                ShopUser.tg_id == tg_id,
            )
            .order_by(ShopTransaction.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_transaction_by_id(self, *, shop_id: int, transaction_db_id: int) -> ShopTransaction | None:
        stmt = (
            select(ShopTransaction)
            .options(selectinload(ShopTransaction.user))
            .where(
                ShopTransaction.shop_id == shop_id,
                ShopTransaction.id == transaction_db_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_transaction_by_payment_system_id(
        self,
        *,
        shop_id: int,
        transaction_id: str,
    ) -> ShopTransaction | None:
        stmt = (
            select(ShopTransaction)
            .options(selectinload(ShopTransaction.user))
            .where(
                ShopTransaction.shop_id == shop_id,
                ShopTransaction.transaction_id == transaction_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_transaction_as_paid(
        self,
        *,
        shop_id: int,
        transaction_id: str,
        paid_at: datetime | None = None,
    ) -> None:
        stmt = (
            select(ShopTransaction)
            .where(
                ShopTransaction.shop_id == shop_id,
                ShopTransaction.transaction_id == transaction_id,
            )
            .with_for_update()
        )
        tx = (await self.session.execute(stmt)).scalar_one_or_none()
        if not tx:
            return

        tx.paid = True
        tx.paid_at = paid_at or datetime.now()
        await self.session.flush()

    async def get_last_transaction(self, *, shop_id: int, tg_id: int) -> ShopTransaction | None:
        stmt = (
            select(ShopTransaction)
            .join(ShopUser, ShopUser.id == ShopTransaction.user_id)
            .where(
                ShopTransaction.shop_id == shop_id,
                ShopUser.shop_id == shop_id,
                ShopUser.tg_id == tg_id,
            )
            .order_by(ShopTransaction.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_transactions(self, *, shop_id: int) -> list[ShopTransaction]:
        result = await self.session.execute(
            select(ShopTransaction)
            .where(ShopTransaction.shop_id == shop_id)
            .order_by(ShopTransaction.created_at.desc())
        )
        return result.scalars().all()
