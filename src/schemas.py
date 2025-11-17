"""Pydantic schemas for API requests/responses"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel


# User schemas (FastAPI-Users)
class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data"""

    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user"""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user"""

    pass


# User profile schemas
class UserProfileRead(BaseModel):
    """Schema for reading user profile"""

    user_id: UUID
    age: Optional[int] = None
    sex: Optional[str] = None
    experience_level: Optional[str] = None
    equipment_access: list[str] = []
    injuries: Optional[str] = None
    time_availability: Optional[int] = None
    preferences: dict = {}
    updated_at: datetime


class UserProfileCreate(BaseModel):
    """Schema for creating user profile"""

    age: Optional[int] = None
    sex: Optional[str] = None
    experience_level: Optional[str] = None
    equipment_access: list[str] = []
    injuries: Optional[str] = None
    time_availability: Optional[int] = None
    preferences: dict = {}


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""

    age: Optional[int] = None
    sex: Optional[str] = None
    experience_level: Optional[str] = None
    equipment_access: Optional[list[str]] = None
    injuries: Optional[str] = None
    time_availability: Optional[int] = None
    preferences: Optional[dict] = None


# Weight log schemas
class WeightLogCreate(BaseModel):
    """Schema for creating weight log"""

    date: datetime
    weight_lbs: Optional[float] = None
    body_fat_pct: Optional[float] = None
    measurements: dict = {}


class WeightLogRead(BaseModel):
    """Schema for reading weight log"""

    id: int
    user_id: UUID
    date: datetime
    weight_lbs: Optional[float] = None
    body_fat_pct: Optional[float] = None
    measurements: dict = {}
    created_at: datetime


# Meal log schemas
class MealLogCreate(BaseModel):
    """Schema for creating meal log"""

    date: datetime
    meal_type: Optional[str] = None
    description: Optional[str] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    calories: Optional[int] = None


class MealLogRead(BaseModel):
    """Schema for reading meal log"""

    id: int
    user_id: UUID
    date: datetime
    meal_type: Optional[str] = None
    description: Optional[str] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    calories: Optional[int] = None
    created_at: datetime


# Workout session schemas
class WorkoutSessionCreate(BaseModel):
    """Schema for creating workout session"""

    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    overall_rpe: Optional[int] = None
    notes: Optional[str] = None


class WorkoutSessionRead(BaseModel):
    """Schema for reading workout session"""

    id: int
    user_id: UUID
    workout_plan_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    overall_rpe: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
