from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from backend.api import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TelegramShop Admin API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == "/api/admin/me":
            print("ROUTE:", r.path, "->", r.endpoint)

    return app


app = create_app()
