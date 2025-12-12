from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    login: str
    full_name: Optional[str] = None
    disabled: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class User(UserBase):
    id: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    login: Optional[str] = None


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    kind: Literal["income", "expense"]

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kind: Optional[Literal["income", "expense"]] = None


class Category(CategoryBase):
    id: int
    owner_id: int


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    category_id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    occurred_at: Optional[datetime] = None
    category_id: Optional[int] = None


class Transaction(TransactionBase):
    id: int
    owner_id: int


class SummaryRow(BaseModel):
    category_id: int
    category_name: str
    kind: Literal["income", "expense"]
    total: Decimal


class SummaryResponse(BaseModel):
    income_total: Decimal
    expense_total: Decimal
    rows: list[SummaryRow]