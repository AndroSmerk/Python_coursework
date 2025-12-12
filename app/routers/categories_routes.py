from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auth, models
from ..db import get_session
from ..entities import Category

router = APIRouter(tags=["categories"])


@router.post(
    "/categories",
    response_model=models.Category,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию",
    description="Добавляет новую категорию доходов или расходов.",
)
async def create_category(
    payload: models.CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Category:
    category = Category(
        name=payload.name,
        kind=payload.kind,
        owner_id=current_user.id,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return models.Category.model_validate(category)


@router.get(
    "/categories",
    response_model=list[models.Category],
    summary="Мои категории",
    description="Возвращает список категорий пользователя.",
)
async def list_categories(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[models.Category]:
    stmt = select(Category).where(Category.owner_id == current_user.id)
    result = await session.execute(stmt)
    categories = result.scalars().all()
    return [models.Category.model_validate(cat) for cat in categories]


async def _get_category_or_404(
    session: AsyncSession, category_id: int, user_id: int
) -> Category:
    stmt = select(Category).where(
        Category.id == category_id, Category.owner_id == user_id
    )
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.get(
    "/categories/{category_id}",
    response_model=models.Category,
    summary="Категория по id",
)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Category:
    category = await _get_category_or_404(session, category_id, current_user.id)
    return models.Category.model_validate(category)


@router.put(
    "/categories/{category_id}",
    response_model=models.Category,
    summary="Обновить категорию",
)
async def update_category(
    category_id: int,
    payload: models.CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Category:
    category = await _get_category_or_404(session, category_id, current_user.id)
    category.name = payload.name
    category.kind = payload.kind
    await session.commit()
    await session.refresh(category)
    return models.Category.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить категорию",
)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> None:
    category = await _get_category_or_404(session, category_id, current_user.id)
    await session.delete(category)
    await session.commit()
    return None


