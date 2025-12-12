from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auth, models
from ..db import get_session
from ..entities import Category, Transaction

router = APIRouter(tags=["transactions"])


async def _get_transaction_or_404(
    session: AsyncSession, tx_id: int, user_id: int
) -> Transaction:
    stmt = select(Transaction).where(
        Transaction.id == tx_id, Transaction.owner_id == user_id
    )
    result = await session.execute(stmt)
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


async def _ensure_category_for_user(
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


@router.post(
    "/transactions",
    response_model=models.Transaction,
    status_code=status.HTTP_201_CREATED,
    summary="Новая операция",
    description="Создает запись о доходе или расходе.",
)
async def create_transaction(
    payload: models.TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Transaction:
    await _ensure_category_for_user(session, payload.category_id, current_user.id)
    tx = Transaction(
        amount=payload.amount,
        description=payload.description,
        occurred_at=payload.occurred_at,
        category_id=payload.category_id,
        owner_id=current_user.id,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return models.Transaction.model_validate(tx)


@router.get(
    "/transactions",
    response_model=list[models.Transaction],
    summary="Мои операции",
    description="Возвращает доходы и расходы текущего пользователя.",
)
async def list_transactions(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[models.Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.owner_id == current_user.id)
        .order_by(Transaction.occurred_at.desc())
    )
    result = await session.execute(stmt)
    txs = result.scalars().all()
    return [models.Transaction.model_validate(tx) for tx in txs]


@router.get(
    "/transactions/summary",
    response_model=models.SummaryResponse,
    summary="Сводка по категориям",
)
async def transaction_summary(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.SummaryResponse:
    stmt = (
        select(
            Category.id,
            Category.name,
            Category.kind,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .join(Transaction, Transaction.category_id == Category.id, isouter=True)
        .where(Category.owner_id == current_user.id)
        .group_by(Category.id)
    )
    result = await session.execute(stmt)
    rows = []
    income_total = 0
    expense_total = 0
    for cat_id, name, kind, total in result:
        total = total or 0
        if kind == "income":
            income_total += total
        else:
            expense_total += total
        rows.append(
            models.SummaryRow(
                category_id=cat_id,
                category_name=name,
                kind=kind,
                total=total,
            )
        )
    return models.SummaryResponse(
        income_total=income_total,
        expense_total=expense_total,
        rows=rows,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=models.Transaction,
    summary="Операция по id",
)
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Transaction:
    tx = await _get_transaction_or_404(session, transaction_id, current_user.id)
    return models.Transaction.model_validate(tx)


@router.put(
    "/transactions/{transaction_id}",
    response_model=models.Transaction,
    summary="Обновить операцию",
)
async def update_transaction(
    transaction_id: int,
    payload: models.TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.Transaction:
    tx = await _get_transaction_or_404(session, transaction_id, current_user.id)
    await _ensure_category_for_user(session, payload.category_id, current_user.id)
    tx.amount = payload.amount
    tx.description = payload.description
    tx.occurred_at = payload.occurred_at
    tx.category_id = payload.category_id
    await session.commit()
    await session.refresh(tx)
    return models.Transaction.model_validate(tx)


@router.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить операцию",
)
async def delete_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
) -> None:
    tx = await _get_transaction_or_404(session, transaction_id, current_user.id)
    await session.delete(tx)
    await session.commit()
    return None


