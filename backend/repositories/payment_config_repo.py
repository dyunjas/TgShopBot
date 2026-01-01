from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ShopPaymentConfig


class PaymentConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, shop_id: int, provider: str) -> ShopPaymentConfig | None:

        stmt = (
            select(ShopPaymentConfig)
            .where(
                ShopPaymentConfig.shop_id == shop_id,
                ShopPaymentConfig.provider == provider,
                ShopPaymentConfig.is_active.is_(True),
            )
        )
        return await self.session.scalar(stmt)