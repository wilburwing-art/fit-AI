"""Data export endpoints: JSON and CSV downloads"""

import csv
import io
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlmodel import select

from src.auth import current_active_user
from src.database import DatabaseSession
from src.models import (
    ExerciseLog,
    MealLog,
    User,
    UserProfile,
    WeightLog,
    WorkoutSession,
)

router = APIRouter()


async def _gather_export_data(
    session: DatabaseSession,
    user: User,
    days: int,
) -> dict:
    """Gather all user data for export within the given date range."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    cutoff = cutoff.replace(tzinfo=None)

    # Weight logs
    weight_result = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user.id, WeightLog.date >= cutoff)
        .order_by(WeightLog.date)
    )
    weight_logs = [
        {
            "date": w.date.isoformat() if w.date else None,
            "weight_lbs": w.weight_lbs,
            "body_fat_pct": w.body_fat_pct,
            "measurements": w.measurements or {},
        }
        for w in weight_result.scalars().all()
    ]

    # Meal logs
    meal_result = await session.execute(
        select(MealLog)
        .where(MealLog.user_id == user.id, MealLog.date >= cutoff)
        .order_by(MealLog.date)
    )
    meal_logs = [
        {
            "date": m.date.isoformat() if m.date else None,
            "meal_type": m.meal_type,
            "description": m.description,
            "protein_g": m.protein_g,
            "carbs_g": m.carbs_g,
            "fat_g": m.fat_g,
            "calories": m.calories,
        }
        for m in meal_result.scalars().all()
    ]

    # Workout sessions
    workout_result = await session.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_date >= cutoff,
        )
        .order_by(WorkoutSession.completed_date)
    )
    workouts = workout_result.scalars().all()
    workout_sessions = [
        {
            "id": w.id,
            "completed_date": w.completed_date.isoformat()
            if w.completed_date
            else None,
            "duration_minutes": w.duration_minutes,
            "overall_rpe": w.overall_rpe,
            "notes": w.notes,
        }
        for w in workouts
    ]

    # Exercise logs for those sessions
    exercise_logs = []
    session_ids = [w.id for w in workouts]
    if session_ids:
        logs_result = await session.execute(
            select(ExerciseLog).where(ExerciseLog.workout_session_id.in_(session_ids))
        )
        exercise_logs = [
            {
                "workout_session_id": el.workout_session_id,
                "exercise_id": el.exercise_id,
                "sets_data": el.sets_data or [],
                "notes": el.notes,
            }
            for el in logs_result.scalars().all()
        ]

    # Profile
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_data = None
    if profile:
        profile_data = {
            "age": profile.age,
            "sex": profile.sex,
            "experience_level": profile.experience_level,
            "equipment_access": profile.equipment_access or [],
            "preferences": profile.preferences or {},
        }

    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "days": days,
        "profile": profile_data,
        "weight_logs": weight_logs,
        "meal_logs": meal_logs,
        "workout_sessions": workout_sessions,
        "exercise_logs": exercise_logs,
    }


@router.get("/json")
async def export_json(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    days: int = Query(default=90, ge=1, le=365),
):
    """Export all user data as JSON download."""
    import json

    data = await _gather_export_data(session, user, days)
    content = json.dumps(data, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=fit_agent_export_{days}d.json"
        },
    )


@router.get("/csv")
async def export_csv(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    days: int = Query(default=90, ge=1, le=365),
):
    """Export user data as CSV download with sections."""
    data = await _gather_export_data(session, user, days)

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)

        # Weight logs section
        writer.writerow(["# Weight Logs"])
        writer.writerow(["date", "weight_lbs", "body_fat_pct"])
        for w in data["weight_logs"]:
            writer.writerow([w["date"], w["weight_lbs"], w["body_fat_pct"]])
        writer.writerow([])

        # Meal logs section
        writer.writerow(["# Meal Logs"])
        writer.writerow(
            [
                "date",
                "meal_type",
                "description",
                "protein_g",
                "carbs_g",
                "fat_g",
                "calories",
            ]
        )
        for m in data["meal_logs"]:
            writer.writerow(
                [
                    m["date"],
                    m["meal_type"],
                    m["description"],
                    m["protein_g"],
                    m["carbs_g"],
                    m["fat_g"],
                    m["calories"],
                ]
            )
        writer.writerow([])

        # Workout sessions section
        writer.writerow(["# Workout Sessions"])
        writer.writerow(
            ["id", "completed_date", "duration_minutes", "overall_rpe", "notes"]
        )
        for w in data["workout_sessions"]:
            writer.writerow(
                [
                    w["id"],
                    w["completed_date"],
                    w["duration_minutes"],
                    w["overall_rpe"],
                    w["notes"],
                ]
            )

        yield output.getvalue()
        output.close()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=fit_agent_export_{days}d.csv"
        },
    )
