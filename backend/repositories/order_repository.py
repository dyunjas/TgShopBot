from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import ShopOrder, ShopUser, AdminUser


def generate_order_id(order_db_id: int) -> str:
    return f"ORD-{order_db_id:06d}"


class ShopOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(
        self,
        *,
        shop_id: int,
        title: str,
        price: int,
        tg_id: int,
        created_at: datetime | None = None,
    ) -> ShopOrder:
        stmt = select(ShopUser.id).where(
            ShopUser.shop_id == shop_id,
            ShopUser.tg_id == tg_id,
        )
        user_id = (await self.session.execute(stmt)).scalar_one_or_none()
        if user_id is None:
            raise ValueError(f"User with tg_id={tg_id} not found in shop_id={shop_id}")

        order = ShopOrder(
            shop_id=shop_id,
            order_id="",
            title=title,
            price=price,
            user_id=user_id,
            created_at=created_at or datetime.now(),
            status="paid",
        )
        self.session.add(order)
        await self.session.flush()

        order.order_id = generate_order_id(order.id)
        await self.session.flush()

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_orders(self, *, shop_id: int, tg_id: int) -> list[ShopOrder]:
        stmt = (
            select(ShopOrder)
            .join(ShopUser, ShopUser.id == ShopOrder.user_id)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopUser.shop_id == shop_id,
                ShopUser.tg_id == tg_id,
            )
            .order_by(ShopOrder.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_all_orders(self, *, shop_id: int) -> list[ShopOrder]:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.shop_id == shop_id)
            .order_by(ShopOrder.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_order_by_id(self, *, shop_id: int, order_db_id: int) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.id == order_db_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_order_by_order_id(self, *, shop_id: int, order_id: str) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def set_drop_card(
        self,
        *,
        shop_id: int,
        order_id: str,
        drop_group_chat_id: int,
        drop_topic_id: int,
        admin_card_msg_id: int,
    ) -> None:
        stmt = (
            select(ShopOrder)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
            .with_for_update()
        )
        order = (await self.session.execute(stmt)).scalar_one_or_none()
        if not order:
            return

        order.drop_group_chat_id = drop_group_chat_id
        order.drop_topic_id = drop_topic_id
        order.admin_card_msg_id = admin_card_msg_id

        await self.session.flush()
        await self.session.commit()

    async def take_order(
        self,
        *,
        shop_id: int,
        order_id: str,
        executor_admin_id: int,
        executor_name: str,
    ) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
            .with_for_update()
        )
        order = (await self.session.execute(stmt)).scalar_one_or_none()
        if not order:
            return None

        if order.executor_admin_id is not None:
            return None

        order.executor_admin_id = executor_admin_id
        order.executor_name = executor_name
        order.status = "in_work"

        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def set_status(self, *, shop_id: int, order_id: str, status: str) -> None:
        stmt = (
            select(ShopOrder)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
            .with_for_update()
        )
        order = (await self.session.execute(stmt)).scalar_one_or_none()
        if not order:
            return
        order.status = status
        await self.session.flush()
        await self.session.commit()

    async def set_review(self, *, shop_id: int, order_id: str, rating: int, review_text: str) -> None:
        stmt = (
            select(ShopOrder)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
            .with_for_update()
        )
        order = (await self.session.execute(stmt)).scalar_one_or_none()
        if not order:
            return
        order.rating = rating
        order.review_text = review_text
        await self.session.flush()
        await self.session.commit()

    async def get_executor_tg_id(self, *, shop_id: int, order_id: str) -> int | None:
        stmt = (
            select(AdminUser.tg_id)
            .join(ShopOrder, ShopOrder.executor_admin_id == AdminUser.id)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_tg_id_by_order(self, *, shop_id: int, order_id: str) -> int | None:

        stmt = (
            select(ShopUser.tg_id)
            .join(ShopOrder, ShopOrder.user_id == ShopUser.id)
            .where(
                ShopOrder.shop_id == shop_id,
                ShopOrder.order_id == order_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_last_open_order_for_user(self, *, shop_id: int, tg_id: int) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .join(ShopUser, ShopUser.id == ShopOrder.user_id)
            .options(selectinload(ShopOrder.user))
            .where(
                ShopOrder.shop_id == shop_id,
                ShopUser.shop_id == shop_id,
                ShopUser.tg_id == tg_id,
                ShopOrder.drop_topic_id.isnot(None),
                ShopOrder.drop_group_chat_id.isnot(None),
                ShopOrder.status.in_(("paid", "in_work")),
            )
            .order_by(ShopOrder.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_drop_topic_id(self, topic_id: int) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.drop_topic_id == topic_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
