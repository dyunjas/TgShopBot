from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .auth import get_session
from .utils.admin_role import CurrentAdmin, require_role

from backend.repositories.shop_repository import ShopRepository, DeleteCategoryResult
from backend.database.models import ShopCategory, ShopItem

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


def get_repo(session: AsyncSession = Depends(get_session)) -> ShopRepository:
    return ShopRepository(session)


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    shop_id: int = Query(...),
    parent_id: Optional[int] = Query(default=None),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    cats = await repo.get_categories(shop_id=shop_id, parent_id=parent_id)
    return cats


@router.post("/categories", response_model=CategoryOut)
async def create_category(
    payload: CategoryCreateIn,
    session: AsyncSession = Depends(get_session),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=payload.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    try:
        cat = await repo.create_category(
            shop_id=payload.shop_id,
            title=payload.title,
            img=payload.img,
            parent_id=payload.parent_id,
        )
        await session.commit()
        return cat
    except ValueError as e:
        await session.rollback()
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
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    try:
        cat = await repo.update_category(
            shop_id=shop_id,
            category_id=category_id,
            title=payload.title,
            img=payload.img,
            parent_id=payload.parent_id,
        )
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

        await session.commit()
        return cat
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Category title conflict for this shop")


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    res = await repo.delete_category(shop_id=shop_id, category_id=category_id)

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
    session: AsyncSession = Depends(get_session),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    repo = ShopRepository(session)

    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if category_id is None:
        return await repo.get_items(shop_id=shop_id)

    cat = await repo.get_category_by_id(shop_id=shop_id, category_id=category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    return await repo.get_items_by_category(shop_id=shop_id, category_id=category_id)


@router.get("/items/{item_id}", response_model=ItemOut)
async def get_item(
    item_id: int,
    shop_id: int = Query(...),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    item = await repo.get_item_by_id(shop_id=shop_id, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/items", response_model=ItemOut)
async def create_item(
    payload: ItemCreateIn,
    session: AsyncSession = Depends(get_session),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=payload.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    try:
        item = await repo.create_item(
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
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/items/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdateIn,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    try:
        item = await repo.update_item(
            shop_id=shop_id,
            item_id=item_id,
            title=payload.title,
            price=payload.price,
            description=payload.description,
            img=payload.img,
            category_id=payload.category_id,
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        await session.commit()
        return item
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    shop_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    repo: ShopRepository = Depends(get_repo),
    _: CurrentAdmin = Depends(require_role("superadmin")),
):
    shop = await repo.get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    ok = await repo.delete_item(shop_id=shop_id, item_id=item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.commit()
    return {"ok": True}
