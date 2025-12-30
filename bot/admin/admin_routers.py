from aiogram import Router
from .broadcast import broadcast
from .orders import orders
from .transactions import transactions
from .shop_management import (
    category_create,
    delete_item,
    item_create,
    subcategory_create
)
from .order_execution import (
    executor_process,
    user_process
)
from bot.admin import admin
router = Router()

router.include_router(broadcast.router)
router.include_router(orders.router)
router.include_router(transactions.router)
router.include_router(category_create.router)
router.include_router(delete_item.router)
router.include_router(item_create.router)
router.include_router(subcategory_create.router)
router.include_router(executor_process.router)
router.include_router(user_process.router)
router.include_router(admin.router)
