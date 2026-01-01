from aiogram import Router

from orderdrop_bot import handlers
from orderdrop_bot import reviews

router = Router()

router.include_router(handlers.router)
router.include_router(reviews.router)
