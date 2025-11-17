"""Data logging API endpoints"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from src.auth import current_active_user
from src.database import DatabaseSession
from src.models import MealLog, User, WeightLog, WorkoutSession
from src.schemas import (
    MealLogCreate,
    MealLogRead,
    WeightLogCreate,
    WeightLogRead,
    WorkoutSessionCreate,
    WorkoutSessionRead,
)

router = APIRouter()


# Weight logging endpoints
@router.post("/weight", response_model=WeightLogRead)
async def log_weight(
    weight_data: WeightLogCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log body weight and measurements"""
    weight_log = WeightLog(
        user_id=user.id,
        date=weight_data.date,
        weight_lbs=weight_data.weight_lbs,
        body_fat_pct=weight_data.body_fat_pct,
        measurements=weight_data.measurements,
    )
    session.add(weight_log)
    await session.commit()
    await session.refresh(weight_log)
    return weight_log


@router.get("/weight", response_model=List[WeightLogRead])
async def get_weight_logs(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 30,
):
    """Get recent weight logs for the current user"""
    result = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user.id)
        .order_by(WeightLog.date.desc())
        .limit(limit)
    )
    weight_logs = result.scalars().all()
    return weight_logs


# Meal logging endpoints
@router.post("/meals", response_model=MealLogRead)
async def log_meal(
    meal_data: MealLogCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log a meal with nutrition data"""
    meal_log = MealLog(
        user_id=user.id,
        date=meal_data.date,
        meal_type=meal_data.meal_type,
        description=meal_data.description,
        protein_g=meal_data.protein_g,
        carbs_g=meal_data.carbs_g,
        fat_g=meal_data.fat_g,
        calories=meal_data.calories,
    )
    session.add(meal_log)
    await session.commit()
    await session.refresh(meal_log)
    return meal_log


@router.get("/meals", response_model=List[MealLogRead])
async def get_meal_logs(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 50,
):
    """Get recent meal logs for the current user"""
    result = await session.execute(
        select(MealLog)
        .where(MealLog.user_id == user.id)
        .order_by(MealLog.date.desc())
        .limit(limit)
    )
    meal_logs = result.scalars().all()
    return meal_logs


# Workout logging endpoints
@router.post("/workouts", response_model=WorkoutSessionRead)
async def log_workout(
    workout_data: WorkoutSessionCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log a workout session"""
    workout_session = WorkoutSession(
        user_id=user.id,
        scheduled_date=workout_data.scheduled_date,
        completed_date=workout_data.completed_date or datetime.utcnow(),
        duration_minutes=workout_data.duration_minutes,
        overall_rpe=workout_data.overall_rpe,
        notes=workout_data.notes,
    )
    session.add(workout_session)
    await session.commit()
    await session.refresh(workout_session)
    return workout_session


@router.get("/workouts", response_model=List[WorkoutSessionRead])
async def get_workout_sessions(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 30,
):
    """Get recent workout sessions for the current user"""
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.completed_date.desc())
        .limit(limit)
    )
    workout_sessions = result.scalars().all()
    return workout_sessions
