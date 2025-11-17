"""Workout-related models"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class WorkoutPlan(SQLModel, table=True):
    """AI-generated workout plans (versioned)"""

    __tablename__ = "workout_plans"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    version: int
    start_date: datetime
    end_date: datetime
    plan_data: dict = Field(sa_column=Column(JSON))
    ai_rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Exercise(SQLModel, table=True):
    """Exercise library"""

    __tablename__ = "exercises"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, unique=True)
    category: Optional[str] = Field(
        default=None, max_length=50
    )  # compound, isolation, cardio
    muscle_groups: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(Text))
    )
    equipment_required: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(Text))
    )
    difficulty: Optional[str] = Field(default=None, max_length=20)
    form_cues: Optional[str] = None
    video_url: Optional[str] = Field(default=None, max_length=500)


class WorkoutSession(SQLModel, table=True):
    """Individual workout sessions"""

    __tablename__ = "workout_sessions"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    workout_plan_id: Optional[int] = Field(default=None, foreign_key="workout_plans.id")
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = Field(default=None, index=True)
    duration_minutes: Optional[int] = None
    overall_rpe: Optional[int] = None  # 1-10
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExerciseLog(SQLModel, table=True):
    """Individual exercise logs within a workout"""

    __tablename__ = "exercise_logs"

    id: int = Field(primary_key=True)
    workout_session_id: int = Field(foreign_key="workout_sessions.id", index=True)
    exercise_id: int = Field(foreign_key="exercises.id")
    sets_data: list[dict] = Field(sa_column=Column(JSON))
    notes: Optional[str] = None
