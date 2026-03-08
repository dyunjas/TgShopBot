from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role

from backend.repositories.category_repository import DeleteCategoryResult
from backend.services.catalog import CatalogService
from backend.services.s3_storage import S3ConfigError, S3InvalidImageError, S3StorageService

router = APIRouter(tags=["catalog"])



class CategoryOut(BaseModel):
    id: int
    shop_id: int
    title: str
    img: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class CategoryCreateIn(BaseModel):
    shop_id: int
    title: str = Field(min_length=1, max_length=32)
    img: str = Field(min_length=1, max_length=255)
    parent_id: Optional[int] = None


class CategoryUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=32)
    img: Optional[str] = Field(default=None, min_length=1, max_length=255)
    parent_id: Optional[int] = None


class ItemOut(BaseModel):
    id: int
    shop_id: int
    created_at: Optional[datetime] = None
    category_id: int
    title: str
    price: int
    description: Optional[str] = None
    img: str

    class Config:
        from_attributes = True


class ItemCreateIn(BaseModel):
    shop_id: int
    category_id: int
    title: str = Field(min_length=1, max_length=64)
    price: int = Field(ge=0)
    description: Optional[str] = None
    img: str = Field(min_length=1, max_length=255)


class ItemUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=64)
    price: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    img: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category_id: Optional[int] = None


class MediaOut(BaseModel):
    key: str
    url: str


def get_catalog_service(session: AsyncSession = Depends(get_session)) -> CatalogService:
    return CatalogService(session)


def dump_unset_aware(payload: BaseModel) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=True)
    return payload.dict(exclude_unset=True)


def get_storage() -> S3StorageService:
    return S3StorageService()


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    shop_id: int = Query(...),
    parent_id: Optional[int] = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.list_categories(shop_id=shop_id, parent_id=parent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")


@router.post("/categories", response_model=CategoryOut)
async def create_category(
    payload: CategoryCreateIn,
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        cat = await service.create_category(
            shop_id=payload.shop_id,
            title=payload.title,
            img=payload.img,
            parent_id=payload.parent_id,
        )
        await session.commit()
        return cat
    except ValueError as e:
        await session.rollback()
        if str(e) == "Shop not found":
            raise HTTPException(status_code=404, detail="Shop not found")
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Category with this title already exists in this shop")


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    payload: CategoryUpdateIn,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        cat = await service.update_category(
            shop_id=shop_id,
            category_id=category_id,
            data=dump_unset_aware(payload),
        )
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

        await session.commit()
        return cat
    except ValueError as e:
        await session.rollback()
        if str(e) == "Shop not found":
            raise HTTPException(status_code=404, detail="Shop not found")
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Category title conflict for this shop")


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        res = await service.delete_category(shop_id=shop_id, category_id=category_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")

    if res == DeleteCategoryResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Category not found")
    if res == DeleteCategoryResult.HAS_ITEMS:
        raise HTTPException(status_code=400, detail="Category has items, cannot delete")
    if res == DeleteCategoryResult.HAS_SUBCATEGORIES:
        raise HTTPException(status_code=400, detail="Category has subcategories, cannot delete")

    await session.commit()
    return {"ok": True}



@router.get("/items", response_model=list[ItemOut])
async def list_items(
    shop_id: int = Query(...),
    category_id: Optional[int] = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        return await service.list_items(shop_id=shop_id, category_id=category_id)
    except ValueError as e:
        detail = "Shop not found" if str(e) == "Shop not found" else str(e)
        code = 404 if detail in ("Shop not found", "Category not found") else 400
        raise HTTPException(status_code=code, detail=detail)


@router.get("/items/{item_id}", response_model=ItemOut)
async def get_item(
    item_id: int,
    shop_id: int = Query(...),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        item = await service.get_item(shop_id=shop_id, item_id=item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/items", response_model=ItemOut)
async def create_item(
    payload: ItemCreateIn,
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        item = await service.create_item(
            shop_id=payload.shop_id,
            title=payload.title,
            price=payload.price,
            description=payload.description,
            img=payload.img,
            category_id=payload.category_id,
        )
        await session.commit()
        return item
    except ValueError as e:
        await session.rollback()
        if str(e) == "Shop not found":
            raise HTTPException(status_code=404, detail="Shop not found")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/items/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdateIn,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        item = await service.update_item(
            shop_id=shop_id,
            item_id=item_id,
            data=dump_unset_aware(payload),
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        await session.commit()
        return item
    except ValueError as e:
        await session.rollback()
        if str(e) == "Shop not found":
            raise HTTPException(status_code=404, detail="Shop not found")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: CatalogService = Depends(get_catalog_service),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        ok = await service.delete_item(shop_id=shop_id, item_id=item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.commit()
    return {"ok": True}


@router.post("/media/upload", response_model=MediaOut)
async def upload_catalog_media(
    shop_id: int = Query(...),
    entity: str = Query(..., pattern="^(items|categories)$"),
    image: UploadFile = File(...),
    service: CatalogService = Depends(get_catalog_service),
    storage: S3StorageService = Depends(get_storage),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        await service.ensure_shop(shop_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")

    if not image.filename:
        raise HTTPException(status_code=400, detail="Image filename is required")

    try:
        stored = storage.upload_image(
            shop_id=shop_id,
            entity=entity,
            filename=image.filename,
            content_type=image.content_type,
            stream=image.file,
        )
        return MediaOut(key=stored.key, url=stored.url)
    except S3InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except S3ConfigError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await image.close()


@router.get("/media", response_model=list[MediaOut])
async def list_catalog_media(
    shop_id: int = Query(...),
    entity: str = Query(..., pattern="^(items|categories)$"),
    service: CatalogService = Depends(get_catalog_service),
    storage: S3StorageService = Depends(get_storage),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    try:
        await service.ensure_shop(shop_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Shop not found")

    try:
        rows = storage.list_images(shop_id=shop_id, entity=entity)
        return [MediaOut(key=x.key, url=x.url) for x in rows]
    except S3ConfigError as e:
        raise HTTPException(status_code=500, detail=str(e))
