from fastapi import APIRouter

from .auth import router as auth_router
from .admin import router as admin_router
from .shops import router as shops_router
from .catalog import router as catalog_router
from .pages import router as pages_router
from .payments import router as payments_router
from .superadmin import router as superadmin_router
from .transactions import router as transactions_router
from backend.api.broadcast import router as broadcast_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(shops_router, prefix="/shops", tags=["shops"])
router.include_router(catalog_router, prefix="/catalog", tags=["catalog"])
router.include_router(pages_router, prefix="/pages", tags=["pages"])
router.include_router(payments_router, prefix="/payments", tags=["payments"])
router.include_router(superadmin_router, prefix="/superadmin", tags=["superadmin"])
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
router.include_router(broadcast_router, prefix="/broadcast", tags=["broadcast"])
