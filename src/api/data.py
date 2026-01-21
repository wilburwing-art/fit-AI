"""Data logging API endpoints"""

from datetime import UTC, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
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


def time_ago(dt: datetime) -> str:
    """Convert datetime to relative time string"""
    # Treat naive datetime as UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} min ago" if minutes > 1 else "1 min ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hr ago" if hours > 1 else "1 hr ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day ago" if days > 1 else "1 day ago"
    else:
        # For older items, show the date
        return dt.strftime("%b %d, %Y")

router = APIRouter()


# Weight logging endpoints
@router.post("/weight", response_model=WeightLogRead)
async def log_weight(
    weight_data: WeightLogCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log body weight and measurements"""
    try:
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
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log weight: {str(e)}"
        )


@router.get("/weight")
async def get_weight_logs(
    request: Request,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 30,
):
    """Get recent weight logs for the current user"""
    try:
        result = await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.date.desc())
            .limit(limit)
        )
        weight_logs = result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch weight logs: {str(e)}"
        )

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        if not weight_logs:
            return HTMLResponse("<p class='text-sm text-gray-500'>No weight logs yet. Start tracking your weight!</p>")

        html = "<div class='space-y-3'>"
        for weight in weight_logs:
            date_str = time_ago(weight.date)

            html += f"""
            <div class='border-l-4 border-blue-500 pl-4 py-2'>
                <div class='flex justify-between items-start'>
                    <div>
                        <p class='text-2xl font-bold text-gray-900'>{weight.weight_lbs} lbs</p>
                        <div class='text-sm text-gray-500 mt-1'>
                            {date_str}
                            {f" • Body Fat: {weight.body_fat_pct}%" if weight.body_fat_pct else ""}
                        </div>
                    </div>
                </div>
            </div>
            """
        html += "</div>"
        return HTMLResponse(html)

    # Return JSON for API requests
    return [WeightLogRead.model_validate(w) for w in weight_logs]


# Meal logging endpoints
@router.post("/meals", response_model=MealLogRead)
async def log_meal(
    meal_data: MealLogCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log a meal with nutrition data"""
    try:
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
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log meal: {str(e)}"
        )


@router.get("/meals")
async def get_meal_logs(
    request: Request,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 50,
):
    """Get recent meal logs for the current user"""
    try:
        result = await session.execute(
            select(MealLog)
            .where(MealLog.user_id == user.id)
            .order_by(MealLog.date.desc())
            .limit(limit)
        )
        meal_logs = result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch meal logs: {str(e)}"
        )

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        if not meal_logs:
            return HTMLResponse("<p class='text-sm text-gray-500'>No meals logged yet. Start tracking your nutrition!</p>")

        html = "<div class='space-y-3'>"
        for meal in meal_logs:
            date_str = time_ago(meal.date)
            meal_type = meal.meal_type.capitalize() if meal.meal_type else "Meal"

            html += f"""
            <div class='border-l-4 border-green-500 pl-4 py-2'>
                <div class='flex justify-between items-start'>
                    <div>
                        <p class='font-medium text-gray-900'>{meal_type}</p>
                        <p class='text-sm text-gray-700 mt-1'>{meal.description or ""}</p>
                        <div class='text-xs text-gray-500 mt-1'>
                            {date_str}
                            {f" • {meal.calories} cal" if meal.calories else ""}
                            {f" • P:{meal.protein_g}g" if meal.protein_g else ""}
                            {f" C:{meal.carbs_g}g" if meal.carbs_g else ""}
                            {f" F:{meal.fat_g}g" if meal.fat_g else ""}
                        </div>
                    </div>
                </div>
            </div>
            """
        html += "</div>"
        return HTMLResponse(html)

    # Return JSON for API requests
    return [MealLogRead.model_validate(m) for m in meal_logs]


# Workout logging endpoints
@router.post("/workouts", response_model=WorkoutSessionRead)
async def log_workout(
    workout_data: WorkoutSessionCreate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Log a workout session"""
    try:
        workout_session = WorkoutSession(
            user_id=user.id,
            scheduled_date=workout_data.scheduled_date,
            completed_date=workout_data.completed_date or datetime.now(UTC),
            duration_minutes=workout_data.duration_minutes,
            overall_rpe=workout_data.overall_rpe,
            notes=workout_data.notes,
        )
        session.add(workout_session)
        await session.commit()
        await session.refresh(workout_session)
        return workout_session
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log workout: {str(e)}"
        )


@router.get("/workouts")
async def get_workout_sessions(
    request: Request,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    limit: int = 30,
):
    """Get recent workout sessions for the current user"""
    try:
        result = await session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(WorkoutSession.completed_date.desc())
            .limit(limit)
        )
        workout_sessions = result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch workout sessions: {str(e)}"
        )

    # Return HTML for HTMX requests, JSON otherwise
    if request.headers.get("HX-Request"):
        if not workout_sessions:
            return HTMLResponse("<p class='text-sm text-gray-500'>No workouts logged yet. Start tracking your workouts!</p>")

        html = "<div class='space-y-4'>"
        for workout in workout_sessions:
            date_str = time_ago(workout.completed_date)
            html += f"""
            <div class='border-l-4 border-indigo-500 pl-4 py-2'>
                <div class='flex justify-between items-start'>
                    <div>
                        <p class='font-medium text-gray-900'>{date_str}</p>
                        <div class='text-sm text-gray-600 mt-1'>
                            {f"Duration: {workout.duration_minutes} min" if workout.duration_minutes else ""}
                            {f" • RPE: {workout.overall_rpe}/10" if workout.overall_rpe else ""}
                        </div>
                        {f"<p class='text-sm text-gray-700 mt-2'>{workout.notes}</p>" if workout.notes else ""}
                    </div>
                </div>
            </div>
            """
        html += "</div>"
        return HTMLResponse(html)

    # Return JSON for API requests
    return [WorkoutSessionRead.model_validate(w) for w in workout_sessions]


@router.get("/recent-activity")
async def get_recent_activity(
    request: Request,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Get combined recent activity (workouts, meals, weight)"""
    try:
        # Fetch recent items from each category
        workouts_result = await session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(WorkoutSession.completed_date.desc())
            .limit(5)
        )
        workouts = workouts_result.scalars().all()

        meals_result = await session.execute(
            select(MealLog)
            .where(MealLog.user_id == user.id)
            .order_by(MealLog.date.desc())
            .limit(5)
        )
        meals = meals_result.scalars().all()

        weight_result = await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.date.desc())
            .limit(5)
        )
        weights = weight_result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent activity: {str(e)}"
        )

    # Combine and sort by date
    activities = []

    for workout in workouts:
        activities.append({
            'type': 'workout',
            'date': workout.completed_date,
            'data': workout
        })

    for meal in meals:
        activities.append({
            'type': 'meal',
            'date': meal.date,
            'data': meal
        })

    for weight in weights:
        activities.append({
            'type': 'weight',
            'date': weight.date,
            'data': weight
        })

    # Sort by date descending
    activities.sort(key=lambda x: x['date'], reverse=True)
    activities = activities[:10]  # Limit to 10 most recent

    if request.headers.get("HX-Request"):
        if not activities:
            return HTMLResponse("""
                <ul class="divide-y divide-gray-200">
                    <li class="px-4 py-4 sm:px-6">
                        <p class="text-sm text-gray-500">No recent activity. Start logging your workouts, meals, and weight!</p>
                    </li>
                </ul>
            """)

        html = "<ul class='divide-y divide-gray-200'>"
        for activity in activities:
            date_str = time_ago(activity['date'])

            if activity['type'] == 'workout':
                workout = activity['data']
                icon = "🏋️"
                title = "Workout"
                details = f"{workout.duration_minutes} min" if workout.duration_minutes else "Completed"
                if workout.overall_rpe:
                    details += f" • RPE {workout.overall_rpe}/10"

            elif activity['type'] == 'meal':
                meal = activity['data']
                icon = "🍽️"
                title = f"{meal.meal_type.capitalize()}" if meal.meal_type else "Meal"
                details = meal.description or "Logged"
                if meal.calories:
                    details += f" • {meal.calories} cal"

            elif activity['type'] == 'weight':
                weight = activity['data']
                icon = "⚖️"
                title = "Weight"
                details = f"{weight.weight_lbs} lbs" if weight.weight_lbs else "Logged"

            html += f"""
            <li class='px-4 py-4 sm:px-6'>
                <div class='flex items-center space-x-4'>
                    <div class='text-2xl'>{icon}</div>
                    <div class='flex-1 min-w-0'>
                        <p class='text-sm font-medium text-gray-900'>{title}</p>
                        <p class='text-sm text-gray-500'>{details}</p>
                        <p class='text-xs text-gray-400 mt-1'>{date_str}</p>
                    </div>
                </div>
            </li>
            """
        html += "</ul>"
        return HTMLResponse(html)

    # Return JSON for API requests
    return activities
