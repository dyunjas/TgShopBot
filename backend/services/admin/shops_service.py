from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.shop_admin_repository import ShopAdminRepository
from backend.services.runtime import shop_bot_manager


@dataclass
class ShopsService:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.repo = ShopAdminRepository(self.session)

    async def create_shop(
        self,
        *,
        title: str,
        bot_token: str,
        reviews_channel_id: int | None,
        is_active: bool,
    ) -> dict:
        token = bot_token.strip()
        clean_title = title.strip()

        exists = await self.repo.get_by_token(token)
        if exists:
            raise ValueError("Такой токен уже используется другим магазином")

        shop = await self.repo.create(
            title=clean_title,
            bot_token=token,
            reviews_channel_id=int(reviews_channel_id or 0),
            is_active=is_active,
        )

        if shop.is_active:
            await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)

        return self._to_dict(shop)

    async def list_shops(self) -> list[dict]:
        shops = await self.repo.list_all()
        return [self._to_dict(shop) for shop in shops]

    async def update_shop(
        self,
        *,
        shop_id: int,
        title: str | None = None,
        bot_token: str | None = None,
        reviews_channel_id: int | None = None,
        is_active: bool | None = None,
    ) -> dict:
        shop = await self.repo.get_by_id(shop_id)
        if not shop:
            raise LookupError("Магазин не найден")

        old_token = shop.bot_token
        old_active = bool(shop.is_active)

        if title is not None:
            shop.title = title.strip()

        if bot_token is not None:
            new_token = bot_token.strip()
            if new_token != shop.bot_token:
                exists = await self.repo.get_by_token(new_token)
                if exists and exists.id != shop.id:
                    raise ValueError("Такой токен уже используется другим магазином")
                shop.bot_token = new_token

        if reviews_channel_id is not None:
            shop.reviews_channel_id = int(reviews_channel_id)

        if is_active is not None:
            shop.is_active = bool(is_active)

        await self.session.flush()
        await self.session.refresh(shop)

        payload = self._to_dict(shop)
        payload["message"] = "Изменения сохранены"

        if old_active and not shop.is_active:
            await shop_bot_manager.stop_shop(shop_id)
            payload["message"] = "Магазин выключен"
            return payload

        if (not old_active) and shop.is_active:
            await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
            payload["message"] = "Магазин включен"
            return payload

        token_changed = bot_token is not None and shop.bot_token != old_token
        if shop.is_active and token_changed:
            await shop_bot_manager.stop_shop(shop_id)
            await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
            payload["message"] = "Токен обновлен, бот перезапущен"

        return payload

    async def toggle_shop(self, *, shop_id: int, is_active: bool) -> dict:
        shop = await self.repo.get_by_id(shop_id)
        if not shop:
            raise LookupError("Магазин не найден")

        shop.is_active = bool(is_active)
        await self.session.flush()
        await self.session.refresh(shop)

        payload = self._to_dict(shop)
        if shop.is_active:
            await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
            payload["message"] = "Магазин запущен"
            return payload

        await shop_bot_manager.stop_shop(shop.id)
        payload["message"] = "Магазин остановлен"
        return payload

    async def restart_shop(self, *, shop_id: int) -> dict:
        shop = await self.repo.get_by_id(shop_id)
        if not shop:
            raise LookupError("Магазин не найден")
        if not shop.is_active:
            raise ValueError("Магазин выключен. Сначала включите его.")

        await shop_bot_manager.stop_shop(shop.id)
        await shop_bot_manager.start_shop(shop_id=shop.id, token=shop.bot_token, title=shop.title)
        return {"ok": True, "message": "Магазин перезапущен"}

    async def delete_shop(self, *, shop_id: int) -> dict:
        shop = await self.repo.get_by_id(shop_id)
        if not shop:
            raise LookupError("Магазин не найден")

        await shop_bot_manager.stop_shop(shop_id)
        await self.repo.delete(shop_id)
        return {"ok": True, "message": "Магазин удален"}

    @staticmethod
    def _to_dict(shop) -> dict:
        return {
            "id": shop.id,
            "title": shop.title,
            "is_active": shop.is_active,
            "bot_token": shop.bot_token,
            "reviews_channel_id": shop.reviews_channel_id,
        }
