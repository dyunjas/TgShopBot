from aiogram import Router

from .submenu import (
    guarantees,
    questions,
    reviews,
    support
)
from .shop.item_purchase import item_purchase
from .shop.shop_nav import (
    main_categories,
    shop_nav
)
from .profile import (
    orders,
    profile,
    promocode,
    transactions
)
from .payments import (
    input_amount,
    lava,
    pally
)
from .main_menu import menu

router = Router()
router.include_router(guarantees.router)
router.include_router(questions.router)
router.include_router(reviews.router)
router.include_router(support.router)
router.include_router(item_purchase.router)
router.include_router(main_categories.router)
router.include_router(shop_nav.router)
router.include_router(orders.router)
router.include_router(profile.router)
router.include_router(promocode.router)
router.include_router(transactions.router)
router.include_router(input_amount.router)
router.include_router(lava.router)
router.include_router(pally.router)
router.include_router(menu.router)