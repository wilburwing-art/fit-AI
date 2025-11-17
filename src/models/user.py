"""User authentication models"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model for authentication (FastAPI-Users compatible)"""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(SQLModel, table=True):
    """User profile with fitness traits and preferences"""

    __tablename__ = "user_profiles"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    age: Optional[int] = None
    sex: Optional[str] = Field(default=None, max_length=10)
    experience_level: Optional[str] = Field(
        default=None, max_length=50
    )  # beginner, intermediate, advanced
    equipment_access: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(Text))
    )
    injuries: Optional[str] = None
    time_availability: Optional[int] = None  # minutes per week
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Goal(SQLModel, table=True):
    """User goals and targets"""

    __tablename__ = "goals"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    goal_type: str = Field(
        max_length=50
    )  # weight_loss, muscle_gain, strength, endurance
    target_value: Optional[float] = None
    target_date: Optional[datetime] = None
    status: str = Field(default="active", max_length=20)  # active, completed, abandoned
    created_at: datetime = Field(default_factory=datetime.utcnow)
