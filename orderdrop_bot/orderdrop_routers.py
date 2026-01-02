from aiogram import Router

from orderdrop_bot import handlers

router = Router()

router.include_router(handlers.router)
