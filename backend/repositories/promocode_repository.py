from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..database.models import ShopPromocode, ShopPromocodeActivation

from datetime import datetime

class ShopPromocodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_promocode(
            self,
            code: str,
            amount: int,
            usages: int,
            created_at: datetime | None = None
    ) -> ShopPromocode:
        
        promocode = ShopPromocode(
            code=code,
            amount=amount,
            usages=usages,
            created_at=created_at or datetime.now()
        )
        self.session.add(promocode)
        await self.session.commit()
        await self.session.refresh(promocode)
        return promocode
    
    async def activate_promocode(self, code: str, user_id: int) -> ShopPromocode | None:
        stmt = select(ShopPromocode).where(ShopPromocode.code == code)
        result = await self.session.execute(stmt)
        promocode: ShopPromocode | None = result.scalar_one_or_none()

        if not promocode:
            return None

        if promocode.usages <= 0:
            return None

        activation = ShopPromocodeActivation(
            promocode_id=promocode.id,
            user_id=user_id
        )
        self.session.add(activation)

        promocode.usages -= 1

        if promocode.usages == 0:
            promocode.is_activated = True
            promocode.activated_at = datetime.now()

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return None

        await self.session.refresh(promocode)
        return promocode