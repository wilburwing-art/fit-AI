"""AI-powered endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth import current_active_user
from src.models import User
from src.services.ai import generate_workout_plan, generate_nutrition_targets


router = APIRouter()


class WorkoutPlanRequest(BaseModel):
    """Request to generate a workout plan"""

    user_goals: str
    experience_level: str
    equipment_access: list[str]
    time_availability: int
    injuries: str | None = None
    age: int | None = None


class NutritionPlanRequest(BaseModel):
    """Request to generate nutrition targets"""

    user_goals: str
    weight_lbs: float
    activity_level: str
    dietary_preferences: str | None = None


@router.post("/generate-workout-plan")
async def create_workout_plan(
    request: WorkoutPlanRequest,
    user: User = Depends(current_active_user),
):
    """Generate a personalized workout plan using AI"""
    try:
        plan = await generate_workout_plan(
            user_goals=request.user_goals,
            experience_level=request.experience_level,
            equipment_access=request.equipment_access,
            time_availability=request.time_availability,
            injuries=request.injuries,
            age=request.age,
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@router.post("/generate-nutrition-plan")
async def create_nutrition_plan(
    request: NutritionPlanRequest,
    user: User = Depends(current_active_user),
):
    """Generate personalized nutrition targets using AI"""
    try:
        plan = await generate_nutrition_targets(
            user_goals=request.user_goals,
            weight_lbs=request.weight_lbs,
            activity_level=request.activity_level,
            dietary_preferences=request.dietary_preferences,
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")
