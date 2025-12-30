from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy import (
    String,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    Text,
    Integer
)
from datetime import datetime


class Base(DeclarativeBase):
    pass


class ShopUser(Base):
    __tablename__ = "shopusers"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    balance: Mapped[int] = mapped_column(default=0)
    orders_amount: Mapped[int] = mapped_column(default=0)
    lang: Mapped[str] = mapped_column(default="ru")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    orders: Mapped[list["ShopOrder"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    transactions: Mapped[list["ShopTransaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    keys: Mapped[list["ShopUserKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class ShopOrder(Base):
    __tablename__ = "shoporders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(32))
    price: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user_id: Mapped[int] = mapped_column(ForeignKey("shopusers.id"))
    user: Mapped["ShopUser"] = relationship(back_populates="orders")

    status: Mapped[str] = mapped_column(String(16), default="paid") 

    group_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admin_card_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    executor_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("shop_admin_users.id"), nullable=True
    )
    executor_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class ShopCategory(Base):
    __tablename__ = "shopcategories"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(32))
    img: Mapped[str] = mapped_column(nullable=False)

    items: Mapped[list["ShopItem"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan"
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("shopcategories.id"), nullable=True
    )
    parent: Mapped["ShopCategory"] = relationship(
        remote_side=[id],
        back_populates="subcategories"
    )
    subcategories: Mapped[list["ShopCategory"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )

class ShopItem(Base):
    __tablename__ = "shopitems"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(32))
    price: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column(nullable=True)
    img: Mapped[str] = mapped_column(nullable=False)

    category_id: Mapped[int] = mapped_column(ForeignKey("shopcategories.id"))

    category: Mapped["ShopCategory"] = relationship(back_populates="items")

class ShopTransaction(Base):
    __tablename__ = "shoptransactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(255))
    amount: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    payment_system: Mapped[str] = mapped_column(String(32))
    order_id: Mapped[str] = mapped_column()

    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("shopusers.id"))

    user: Mapped["ShopUser"] = relationship(back_populates="transactions")

class ShopPromocode(Base):
    __tablename__ = "shoppromocodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(default=0, nullable=False)
    usages: Mapped[int] = mapped_column(default=1)
    is_activated: Mapped[bool] = mapped_column(default=False)
    activated_at: Mapped[datetime] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    activations: Mapped[list["ShopPromocodeActivation"]] = relationship(
        back_populates="promocode", cascade="all, delete-orphan"
    )

class ShopPromocodeActivation(Base):
    __tablename__ = "shop_promocode_usages"

    id: Mapped[int] = mapped_column(primary_key=True)
    promocode_id: Mapped[int] = mapped_column(ForeignKey("shoppromocodes.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    activated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    promocode: Mapped[ShopPromocode] = relationship(back_populates="activations")

    __table_args__ = (UniqueConstraint("promocode_id", "user_id", name="uq_promocode_user"),)


class ShopUserKey(Base):
    __tablename__ = "shop_user_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("shopusers.id", ondelete="CASCADE"))
    user: Mapped["ShopUser"] = relationship(back_populates="keys")

    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class AdminUser(Base):
    __tablename__ = "shop_admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)