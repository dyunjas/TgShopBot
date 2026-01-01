from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..database.models import ShopPromocode, ShopPromocodeActivation


class ShopPromocodeRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_promocode(
        self,
        *,
        shop_id: int,
        code: str,
        amount: int,
        usages: int,
        created_at: datetime | None = None,
    ) -> ShopPromocode:
        promocode = ShopPromocode(
            shop_id=shop_id,
            code=code,
            amount=amount,
            usages=usages,
            created_at=created_at or datetime.now(),
            is_activated=False,
        )
        self.session.add(promocode)
        await self.session.flush()
        await self.session.refresh(promocode)
        return promocode

    async def activate_promocode(
        self,
        *,
        shop_id: int,
        code: str,
        tg_id: int,
    ) -> ShopPromocode | None:

        stmt = (
            select(ShopPromocode)
            .where(
                ShopPromocode.shop_id == shop_id,
                ShopPromocode.code == code,
            )
            .with_for_update()
        )
        promocode: ShopPromocode | None = (await self.session.execute(stmt)).scalar_one_or_none()

        if not promocode:
            return None

        if promocode.usages <= 0 or promocode.is_activated:
            return None

        activation = ShopPromocodeActivation(
            shop_id=shop_id,
            promocode_id=promocode.id,
            user_id=tg_id, 
            activated_at=datetime.now(),
        )
        self.session.add(activation)

        promocode.usages -= 1
        if promocode.usages <= 0:
            promocode.usages = 0
            promocode.is_activated = True
            promocode.activated_at = datetime.now()

        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            return None

        await self.session.refresh(promocode)
        return promocode
