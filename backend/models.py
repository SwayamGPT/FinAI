from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import datetime

class BaseMoneyModel(BaseModel):
    @validator('*', pre=True)
    def round_floats(cls, v):
        if isinstance(v, float): return round(v, 2)
        return v

class UserAuth(BaseModel):
    username: str
    password: str

class GoogleLoginRequest(BaseModel):
    token: str

class OnboardingModel(BaseMoneyModel):
    age: int
    salary: float
    rent: float
    current_savings: float
    saving_goal: str

class AssetModel(BaseMoneyModel):
    name: str
    type: str 
    value: float
    liquidity_score: int = Field(ge=1, le=5)

class LiabilityModel(BaseMoneyModel):
    name: str
    type: str 
    outstanding_amount: float
    interest_rate: float
    monthly_payment: float

class GoalModel(BaseMoneyModel):
    name: str
    target_amount: float
    target_date: str
    priority: Literal['High', 'Medium', 'Low']

class ExpenseModel(BaseMoneyModel):
    title: str
    amount: float
    category: str = "General"
    date: str = datetime.now().strftime("%Y-%m-%d")

class AdvisorRequest(BaseModel):
    query: str