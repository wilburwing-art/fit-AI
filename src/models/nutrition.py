"""Nutrition and body metrics models"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class WeightLog(SQLModel, table=True):
    """Body weight and measurements"""

    __tablename__ = "weight_logs"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: datetime = Field(index=True)
    weight_lbs: Optional[float] = Field(default=None, max_digits=5, decimal_places=1)
    body_fat_pct: Optional[float] = Field(default=None, max_digits=4, decimal_places=1)
    measurements: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MealLog(SQLModel, table=True):
    """Meal and nutrition logs"""

    __tablename__ = "meal_logs"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: datetime = Field(index=True)
    meal_type: Optional[str] = Field(
        default=None, max_length=20
    )  # breakfast, lunch, dinner, snack
    description: Optional[str] = None
    protein_g: Optional[float] = Field(default=None, max_digits=5, decimal_places=1)
    carbs_g: Optional[float] = Field(default=None, max_digits=5, decimal_places=1)
    fat_g: Optional[float] = Field(default=None, max_digits=5, decimal_places=1)
    calories: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NutritionTarget(SQLModel, table=True):
    """AI-generated nutrition targets"""

    __tablename__ = "nutrition_targets"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    start_date: datetime
    end_date: datetime
    daily_protein_g: int
    daily_carbs_g: int
    daily_fat_g: int
    daily_calories: int
    ai_rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
