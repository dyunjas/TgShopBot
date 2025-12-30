from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..database.models import ShopOrder, ShopUser, AdminUser


def generate_order_id(order_db_id: int) -> str:
    return f"ORD-{order_db_id:06d}"


class ShopOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ====== CREATE ======
    async def create_order(
        self,
        title: str,
        price: int,
        tg_id: int,
        created_at: datetime | None = None
    ) -> ShopOrder:
        stmt = select(ShopUser.id).where(ShopUser.tg_id == tg_id)
        result = await self.session.execute(stmt)
        user_id = result.scalar_one_or_none()
        if user_id is None:
            raise ValueError(f"User with tg_id={tg_id} not found")

        order = ShopOrder(
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

        await self.session.commit()
        await self.session.refresh(order)
        return order

    # ====== OLD METHODS (для твоих старых хендлеров) ======

    async def get_orders(self, tg_id: int) -> list[ShopOrder]:
        """
        История заказов пользователя (order_history).
        """
        stmt = (
            select(ShopOrder)
            .join(ShopUser)
            .where(ShopUser.tg_id == tg_id)
            .order_by(ShopOrder.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_all_orders(self) -> list[ShopOrder]:
        """
        Список всех заказов (админка).
        """
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .order_by(ShopOrder.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_order_by_id(self, order_db_id: int) -> ShopOrder | None:
        """
        Детали заказа по DB id (старые клавиатуры передают int id).
        """
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.id == order_db_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # ====== NEW METHODS (под темы/поддержку) ======

    async def get_order_by_order_id(self, order_id: str) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.order_id == order_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_topic_id(self, topic_id: int) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.topic_id == topic_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def set_admin_topic(
        self,
        order_id: str,
        *,
        group_chat_id: int,
        topic_id: int,
        admin_card_msg_id: int
    ) -> None:
        stmt = select(ShopOrder).where(ShopOrder.order_id == order_id).with_for_update()
        res = await self.session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return

        order.group_chat_id = group_chat_id
        order.topic_id = topic_id
        order.admin_card_msg_id = admin_card_msg_id
        await self.session.commit()

    async def take_order(
        self,
        order_id: str,
        *,
        executor_admin_id: int,
        executor_name: str
    ) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.user))
            .where(ShopOrder.order_id == order_id)
            .with_for_update()
        )
        res = await self.session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return None

        if order.executor_admin_id is not None:
            return None

        order.executor_admin_id = executor_admin_id
        order.executor_name = executor_name
        order.status = "taken"

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def set_status(self, order_id: str, status: str) -> None:
        stmt = select(ShopOrder).where(ShopOrder.order_id == order_id).with_for_update()
        res = await self.session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return
        order.status = status
        await self.session.commit()

    async def set_review(self, order_id: str, *, rating: int, review_text: str) -> None:
        stmt = select(ShopOrder).where(ShopOrder.order_id == order_id).with_for_update()
        res = await self.session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return
        order.rating = rating
        order.review_text = review_text
        await self.session.commit()

    async def get_executor_tg_id(self, order_id: str) -> int | None:
        stmt = (
            select(AdminUser.tg_id)
            .join(ShopOrder, ShopOrder.executor_admin_id == AdminUser.id)
            .where(ShopOrder.order_id == order_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_last_open_order_for_user(self, tg_id: int) -> ShopOrder | None:
        stmt = (
            select(ShopOrder)
            .join(ShopUser)
            .options(selectinload(ShopOrder.user))
            .where(
                ShopUser.tg_id == tg_id,
                ShopOrder.topic_id.isnot(None),
                ShopOrder.group_chat_id.isnot(None),
                ShopOrder.status.in_(("paid", "taken")),
            )
            .order_by(ShopOrder.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
