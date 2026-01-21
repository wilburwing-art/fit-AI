"""AI-powered endpoints"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.auth import current_active_user
from src.exceptions import AIServiceError
from src.models import User
from src.rate_limit import RATE_LIMITS, limiter
from src.services.ai import generate_nutrition_targets, generate_workout_plan

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkoutPlanRequest(BaseModel):
    """Request to generate a workout plan"""

    user_goals: str = Field(..., min_length=1, max_length=1000)
    experience_level: Literal["beginner", "intermediate", "advanced"] = Field(...)
    equipment_access: list[str] = Field(..., max_length=50)
    time_availability: int = Field(
        ..., ge=30, le=600, description="Minutes per week (30-600)"
    )
    injuries: str | None = Field(default=None, max_length=1000)
    age: int | None = Field(default=None, ge=13, le=120)


class NutritionPlanRequest(BaseModel):
    """Request to generate nutrition targets"""

    user_goals: str = Field(..., min_length=1, max_length=1000)
    weight_lbs: float = Field(..., ge=50, le=700, description="Body weight in pounds")
    activity_level: Literal[
        "sedentary", "light", "moderate", "active", "very_active"
    ] = Field(...)
    dietary_preferences: str | None = Field(default=None, max_length=500)


@router.post("/generate-workout-plan")
@limiter.limit(RATE_LIMITS["ai_workout_plan"])
async def create_workout_plan(
    request_data: WorkoutPlanRequest,
    request: Request,
    user: User = Depends(current_active_user),
):
    """Generate a personalized workout plan using AI"""
    try:
        plan = await generate_workout_plan(
            user_goals=request_data.user_goals,
            experience_level=request_data.experience_level,
            equipment_access=request_data.equipment_access,
            time_availability=request_data.time_availability,
            injuries=request_data.injuries,
            age=request_data.age,
        )
        return plan
    except AIServiceError:
        raise
    except Exception as e:
        logger.exception(f"Workout plan generation failed for user {user.id}")
        raise AIServiceError(
            message=f"Workout plan generation failed: {e}",
            user_message="Failed to generate workout plan. Please try again later.",
            details={"user_id": str(user.id)},
        )


@router.post("/generate-nutrition-plan")
@limiter.limit(RATE_LIMITS["ai_nutrition_plan"])
async def create_nutrition_plan(
    request_data: NutritionPlanRequest,
    request: Request,
    user: User = Depends(current_active_user),
):
    """Generate personalized nutrition targets using AI"""
    try:
        plan = await generate_nutrition_targets(
            user_goals=request_data.user_goals,
            weight_lbs=request_data.weight_lbs,
            activity_level=request_data.activity_level,
            dietary_preferences=request_data.dietary_preferences,
        )
        return plan
    except AIServiceError:
        raise
    except Exception as e:
        logger.exception(f"Nutrition plan generation failed for user {user.id}")
        raise AIServiceError(
            message=f"Nutrition plan generation failed: {e}",
            user_message="Failed to generate nutrition plan. Please try again later.",
            details={"user_id": str(user.id)},
        )
