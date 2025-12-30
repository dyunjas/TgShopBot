from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ShopUser

import asyncio 

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from aiogram.types import InlineKeyboardMarkup

class ShopUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
            self,
            tg_id: int,
            username: str | None
    ) -> ShopUser:
        user = ShopUser(
            tg_id=tg_id,
            username=username,
            balance=0,
            lang="ru",
            orders_amount=0
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_user(self, tg_id: int) -> ShopUser | None:
        result = await self.session.execute(
            select(ShopUser).where(ShopUser.tg_id == tg_id)
        )
        return result.scalar_one_or_none()
    
    async def increase_balance(self, tg_id: int, amount: int) -> int:
        user = await self.session.execute(
            select(ShopUser).where(ShopUser.tg_id == tg_id)
        )
        user = user.scalar_one()
        user.balance += amount
        await self.session.commit()
        await self.session.refresh(user)
        return user.balance
    
    async def decrease_balance(self, tg_id: int, amount: int) -> int:
        user = await self.session.execute(
            select(ShopUser).where(ShopUser.tg_id == tg_id)
        )
        user = user.scalar_one()
        user.balance -= amount
        await self.session.commit()
        await self.session.refresh(user)
        return user.balance
    
    async def update_username(self, tg_id: int, new_username: str | None):
        user = await self.session.execute(
            select(ShopUser).where(ShopUser.tg_id == tg_id)
        )
        user = user.scalar_one()
        user.username = new_username
        await self.session.commit()

    async def increase_orders_amount(self, tg_id: int, amount: int) -> int:
        user = await self.session.execute(
            select(ShopUser).where(ShopUser.tg_id == tg_id)
        )
        user = user.scalar_one()
        user.orders_amount += amount
        await self.session.commit()
        await self.session.refresh(user)
        return user.balance
    
    async def broadcast_message(
        self,
        bot: Bot,
        photo_id: str | None,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None
    ):
        result = await self.session.execute(select(ShopUser.tg_id))
        tg_ids = result.scalars().all()

        for tg_id in tg_ids:
            await self.send_safe_message(bot, tg_id, photo_id, text, reply_markup)

    @staticmethod
    async def send_safe_message(
        bot: Bot,
        user_id: int,
        photo_id: str | None,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None
    ):
        try:
            if photo_id:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
        except TelegramBadRequest as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")
        await asyncio.sleep(0.05)