"""Pydantic schemas for API requests/responses"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    weight_lbs: Optional[float] = Field(default=None, ge=50, le=700)
    body_fat_pct: Optional[float] = Field(default=None, ge=1, le=60)
    measurements: dict = {}

    @field_validator("date", mode="before")
    @classmethod
    def strip_timezone(cls, v):
        """Strip timezone info to match database expectations"""
        if isinstance(v, str):
            # Parse ISO string and strip timezone
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class WeightLogRead(BaseModel):
    """Schema for reading weight log"""

    model_config = ConfigDict(from_attributes=True)

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
    meal_type: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=1000)
    protein_g: Optional[float] = Field(default=None, ge=0, le=500)
    carbs_g: Optional[float] = Field(default=None, ge=0, le=1000)
    fat_g: Optional[float] = Field(default=None, ge=0, le=500)
    calories: Optional[int] = Field(default=None, ge=0, le=10000)

    @field_validator("date", mode="before")
    @classmethod
    def strip_timezone(cls, v):
        """Strip timezone info to match database expectations"""
        if isinstance(v, str):
            # Parse ISO string and strip timezone
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class MealLogRead(BaseModel):
    """Schema for reading meal log"""

    model_config = ConfigDict(from_attributes=True)

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
class ExerciseSetData(BaseModel):
    """A single set within an exercise log"""

    weight: Optional[float] = Field(default=None, ge=0)
    reps: Optional[int] = Field(default=None, ge=0)
    rpe: Optional[int] = Field(default=None, ge=1, le=10)


class ExerciseLogCreate(BaseModel):
    """Create an exercise log entry within a workout"""

    exercise_id: int
    sets_data: list[ExerciseSetData] = []
    notes: Optional[str] = None


class WorkoutSessionCreate(BaseModel):
    """Schema for creating workout session"""

    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=480)
    overall_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = Field(default=None, max_length=2000)
    exercise_logs: list[ExerciseLogCreate] = []

    @field_validator("scheduled_date", "completed_date", mode="before")
    @classmethod
    def strip_timezone(cls, v):
        """Strip timezone info to match database expectations"""
        if isinstance(v, str):
            # Parse ISO string and strip timezone
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class WorkoutSessionRead(BaseModel):
    """Schema for reading workout session"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    workout_plan_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    overall_rpe: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


# Exercise schemas
class ExerciseRead(BaseModel):
    """Full exercise detail"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: Optional[str] = None
    name: str
    category: Optional[str] = None
    force: Optional[str] = None
    mechanic: Optional[str] = None
    equipment: Optional[str] = None
    difficulty: Optional[str] = None
    primary_muscles: list[str] = []
    secondary_muscles: list[str] = []
    instructions: list[str] = []
    images: list[str] = []
    form_cues: Optional[str] = None
    video_url: Optional[str] = None
    is_custom: bool = False


class ExerciseSummary(BaseModel):
    """Compact exercise for list/grid views"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str] = None
    equipment: Optional[str] = None
    difficulty: Optional[str] = None
    primary_muscles: list[str] = []
    image: Optional[str] = None


class UserExercisePreferenceCreate(BaseModel):
    """Create a user exercise preference"""

    exercise_id: int
    preference: str = Field(pattern=r"^(favorite|excluded)$")


class UserExercisePreferenceRead(BaseModel):
    """Read a user exercise preference"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    exercise_id: int
    preference: str
    created_at: datetime


# Training preferences
class TrainingPreferencesUpdate(BaseModel):
    """Update training preferences stored in UserProfile.preferences"""

    training_goal: Optional[str] = (
        None  # muscle_gain, strength, weight_loss, endurance, general
    )
    training_split: Optional[str] = (
        None  # full_body, upper_lower, push_pull_legs, bro_split
    )
    days_per_week: Optional[int] = Field(default=None, ge=1, le=7)
    session_duration_minutes: Optional[int] = Field(default=None, ge=15, le=180)
    weekly_volume_target: Optional[int] = None  # total sets per week
    weekly_cardio_minutes: Optional[int] = Field(default=None, ge=0)


# Analytics schemas
class MuscleRecovery(BaseModel):
    """Recovery status for a single muscle group"""

    muscle: str
    last_trained: Optional[str] = None
    hours_since: Optional[float] = None
    recovery_pct: int  # 0-100
    status: str  # "fresh", "recovering", "ready"


class StrengthScore(BaseModel):
    """Strength score for a single exercise"""

    exercise_id: int
    exercise_name: str
    best_weight: Optional[float] = None
    best_reps: Optional[int] = None
    estimated_1rm: Optional[float] = None
    level: str  # "beginner", "intermediate", "advanced", "elite"


class WeeklyProgress(BaseModel):
    """Progress toward a weekly target"""

    metric: str
    label: str
    target: float
    actual: float
    pct: float


class CalendarDay(BaseModel):
    """Workout data for a single calendar day"""

    date: str
    has_workout: bool = False
    workout_count: int = 0
    total_duration: Optional[int] = None
    exercises: list[str] = []


class PersonalRecord(BaseModel):
    """A personal record (PR) for a specific exercise"""

    exercise_id: int
    exercise_name: str
    pr_date: str
    weight: float
    reps: int
    estimated_1rm: float
    previous_1rm: Optional[float] = None
    improvement_pct: Optional[float] = None


class CoachingRequest(BaseModel):
    """Request for AI coaching Q&A"""

    question: str = Field(..., min_length=3, max_length=2000)


class CoachingResponse(BaseModel):
    """Response from AI coaching"""

    answer: str
