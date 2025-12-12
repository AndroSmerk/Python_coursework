from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auth, models
from ..db import get_session
from ..entities import User

router = APIRouter(tags=["auth"])


@router.post(
    "/auth/register",
    response_model=models.User,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Создает нового пользователя и возвращает его данные.",
)
async def register_user(
    payload: models.UserCreate,
    session: AsyncSession = Depends(get_session),
) -> models.User:
    existing = await auth.get_user_by_login(session, payload.login)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    hashed_password = auth.hash_password(payload.password)
    user = User(
        login=payload.login,
        full_name=payload.full_name,
        hashed_password=hashed_password,
        disabled=payload.disabled,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return models.User.model_validate(user)


@router.post(
    "/auth/token",
    response_model=models.Token,
    summary="Login and get JWT",
    description="Возвращает JWT по логину и паролю.",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> models.Token:
    user = await auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    return models.Token(access_token=access_token)


@router.get(
    "/users/me",
    response_model=models.User,
    summary="Get current user",
    description="Возвращает профиль текущего авторизованного пользователя.",
)
async def read_users_me(
    current_user: models.User = Depends(auth.get_current_user),
) -> models.User:
    return current_user


