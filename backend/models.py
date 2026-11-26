from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Money = Field(ge=0)


class BaseMoneyModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def round_floats(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v


def _check_date(v: str) -> str:
    datetime.strptime(v, "%Y-%m-%d")  # raises ValueError -> 422
    return v


class UserAuth(BaseModel):
    """Login payload. Kept lenient so accounts created before validation still work."""
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()


class RegisterModel(UserAuth):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class GoogleLoginRequest(BaseModel):
    token: str


class OnboardingModel(BaseMoneyModel):
    age: int = Field(ge=16, le=120)
    salary: float = Field(gt=0)
    rent: float = Money
    current_savings: float = Money
    saving_goal: str = Field(max_length=200)


class AssetModel(BaseMoneyModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    value: float = Money
    liquidity_score: int = Field(ge=1, le=5)


class LiabilityModel(BaseMoneyModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    outstanding_amount: float = Money
    interest_rate: float = Field(ge=0, le=100)
    monthly_payment: float = Money


class GoalModel(BaseMoneyModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0)
    target_date: str
    priority: Literal["High", "Medium", "Low"] = "Medium"
    saved_amount: float = Field(default=0, ge=0)  # already set aside for this goal (part of your assets)

    @field_validator("target_date")
    @classmethod
    def valid_target_date(cls, v: str) -> str:
        return _check_date(v)


class ExpenseModel(BaseMoneyModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    category: str = Field(default="General", max_length=50)
    # default_factory: evaluated per request, not once at import time
    date: str = Field(default_factory=lambda: date.today().isoformat())

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        return _check_date(v)


class AdvisorRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
