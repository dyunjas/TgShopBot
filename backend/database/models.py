from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    String,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    Text,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import Optional

class Base(DeclarativeBase):
    pass


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    reviews_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    users: Mapped[list["ShopUser"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    categories: Mapped[list["ShopCategory"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    items: Mapped[list["ShopItem"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    orders: Mapped[list["ShopOrder"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    promocodes: Mapped[list["ShopPromocode"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )

    payment_configs: Mapped[list["ShopPaymentConfig"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )

    pages: Mapped[list["ShopPage"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )

    ui_assets: Mapped[Optional["ShopUiAssets"]] = relationship(
        back_populates="shop",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ShopUiAssets(Base):
    __tablename__ = "shop_ui_assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="ui_assets")

    img_topup_menu: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    img_choose_payment_menu: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    img_success_payment_menu: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("shop_id", name="uq_shop_ui_assets_shop_id"),
    )


class ShopPage(Base):
    __tablename__ = "shop_pages"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="pages")

    page_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("shop_id", "page_type", name="uq_shop_page_type"),
    )


class ShopPaymentConfig(Base):
    __tablename__ = "shop_payment_configs"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="payment_configs")

    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    shop_id_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    secret_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    success_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    fail_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    __table_args__ = (
        UniqueConstraint("shop_id", "provider", name="uq_shop_payment_provider"),
    )


class ShopUser(Base):
    __tablename__ = "shopusers"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="users")

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)

    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orders_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lang: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    orders: Mapped[list["ShopOrder"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["ShopTransaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    keys: Mapped[list["ShopUserKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("shop_id", "tg_id", name="uq_shopusers_shop_tg"),
    )


class ShopOrder(Base):
    __tablename__ = "shoporders"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="orders")

    order_id: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("shopusers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user: Mapped["ShopUser"] = relationship(back_populates="orders")

    status: Mapped[str] = mapped_column(String(16), default="paid", nullable=False)

    admin_card_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drop_group_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    drop_topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    executor_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("shop_admin_users.id"),
        nullable=True,
    )
    executor_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("shop_id", "order_id", name="uq_shoporders_shop_orderid"),
    )


class ShopCategory(Base):
    __tablename__ = "shopcategories"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="categories")

    title: Mapped[str] = mapped_column(String(32), nullable=False)
    img: Mapped[str] = mapped_column(String(255), nullable=False)

    items: Mapped[list["ShopItem"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("shopcategories.id", ondelete="CASCADE"),
        nullable=True,
    )
    parent: Mapped["ShopCategory"] = relationship(
        remote_side=[id], back_populates="subcategories"
    )
    subcategories: Mapped[list["ShopCategory"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("shop_id", "title", name="uq_shopcategories_shop_title"),
    )


class ShopItem(Base):
    __tablename__ = "shopitems"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="items")

    title: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    img: Mapped[str] = mapped_column(String(255), nullable=False)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("shopcategories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped["ShopCategory"] = relationship(back_populates="items")


class ShopTransaction(Base):
    __tablename__ = "shoptransactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    payment_system: Mapped[str] = mapped_column(String(32), nullable=False)
    order_id: Mapped[str] = mapped_column(String(32), nullable=False)

    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("shopusers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["ShopUser"] = relationship(back_populates="transactions")

    __table_args__ = (
        UniqueConstraint("shop_id", "transaction_id", name="uq_shoptransactions_shop_tx"),
    )


class ShopPromocode(Base):
    __tablename__ = "shoppromocodes"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["Shop"] = relationship(back_populates="promocodes")

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usages: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    is_activated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    activations: Mapped[list["ShopPromocodeActivation"]] = relationship(
        back_populates="promocode", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("shop_id", "code", name="uq_shoppromocodes_shop_code"),
    )


class ShopPromocodeActivation(Base):
    __tablename__ = "shop_promocode_usages"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    promocode_id: Mapped[int] = mapped_column(
        ForeignKey("shoppromocodes.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    activated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    promocode: Mapped["ShopPromocode"] = relationship(back_populates="activations")

    __table_args__ = (
        UniqueConstraint("shop_id", "promocode_id", "user_id", name="uq_promocode_user_shop"),
    )


class ShopUserKey(Base):
    __tablename__ = "shop_user_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("shopusers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["ShopUser"] = relationship(back_populates="keys")

    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("shop_id", "uuid", name="uq_shop_user_keys_shop_uuid"),
    )


class AdminUser(Base):
    __tablename__ = "shop_admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="operator", nullable=False)

    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AdminLoginCode(Base):
    __tablename__ = "admin_login_codes"

    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    __table_args__ = (
        UniqueConstraint("tg_id", "used_at", name="uq_admin_login_active"),
    )
