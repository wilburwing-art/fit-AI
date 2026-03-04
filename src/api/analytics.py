"""Analytics API: recovery tracking, strength scores, weekly targets, calendar"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import select

from src.auth import current_active_user
from src.database import DatabaseSession
from src.models import (
    Exercise,
    ExerciseLog,
    MealLog,
    User,
    UserProfile,
    WeightLog,
    WorkoutSession,
)
from src.schemas import (
    CalendarDay,
    MuscleRecovery,
    PersonalRecord,
    StrengthScore,
    TrainingPreferencesUpdate,
    WeeklyProgress,
)

router = APIRouter()

# Recovery time constants (hours)
FULL_RECOVERY_HOURS = 72
READY_THRESHOLD_HOURS = 48


@router.get("/recovery")
async def get_recovery_status(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
) -> list[MuscleRecovery]:
    """Get muscle recovery status based on recent workouts."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=FULL_RECOVERY_HOURS)

    # Get recent workout sessions
    sessions_result = await session.execute(
        select(WorkoutSession.id, WorkoutSession.completed_date)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_date >= cutoff,
        )
        .order_by(WorkoutSession.completed_date.desc())
    )
    recent_sessions = sessions_result.all()

    if not recent_sessions:
        return []

    session_ids = [s.id for s in recent_sessions]
    session_dates = {s.id: s.completed_date for s in recent_sessions}

    # Get exercise logs for recent sessions
    logs_result = await session.execute(
        select(ExerciseLog.workout_session_id, ExerciseLog.exercise_id).where(
            ExerciseLog.workout_session_id.in_(session_ids)
        )
    )
    exercise_logs = logs_result.all()

    if not exercise_logs:
        return []

    exercise_ids = list({log.exercise_id for log in exercise_logs})

    # Get exercises with muscle data
    exercises_result = await session.execute(
        select(Exercise.id, Exercise.primary_muscles, Exercise.secondary_muscles).where(
            Exercise.id.in_(exercise_ids)
        )
    )
    exercises = {e.id: e for e in exercises_result.all()}

    # Map muscles to their most recent training time
    muscle_last_trained: dict[str, datetime] = {}
    for log in exercise_logs:
        ex = exercises.get(log.exercise_id)
        if not ex:
            continue
        trained_at = session_dates.get(log.workout_session_id)
        if not trained_at:
            continue
        # Treat naive datetimes as UTC
        if trained_at.tzinfo is None:
            trained_at = trained_at.replace(tzinfo=UTC)
        for muscle in ex.primary_muscles or []:
            existing = muscle_last_trained.get(muscle)
            if existing is None or trained_at > existing:
                muscle_last_trained[muscle] = trained_at

    # Calculate recovery for each muscle
    results = []
    for muscle, last_trained in sorted(muscle_last_trained.items()):
        hours_since = (now - last_trained).total_seconds() / 3600
        recovery_pct = min(100, int((hours_since / FULL_RECOVERY_HOURS) * 100))
        if recovery_pct >= 100:
            status = "fresh"
        elif hours_since >= READY_THRESHOLD_HOURS:
            status = "ready"
        else:
            status = "recovering"

        results.append(
            MuscleRecovery(
                muscle=muscle,
                last_trained=last_trained.strftime("%Y-%m-%d %H:%M"),
                hours_since=round(hours_since, 1),
                recovery_pct=recovery_pct,
                status=status,
            )
        )

    return results


@router.get("/strength")
async def get_strength_scores(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
) -> list[StrengthScore]:
    """Get estimated strength scores from exercise logs."""
    # Get all workout sessions for this user
    sessions_result = await session.execute(
        select(WorkoutSession.id).where(WorkoutSession.user_id == user.id)
    )
    session_ids = [s.id for s in sessions_result.all()]

    if not session_ids:
        return []

    # Get exercise logs with set data
    logs_result = await session.execute(
        select(ExerciseLog).where(ExerciseLog.workout_session_id.in_(session_ids))
    )
    all_logs = logs_result.scalars().all()

    if not all_logs:
        return []

    # Find best set per exercise (highest estimated 1RM)
    exercise_best: dict[int, dict] = {}
    for log in all_logs:
        for set_data in log.sets_data or []:
            weight = set_data.get("weight")
            reps = set_data.get("reps")
            if not weight or not reps or weight <= 0 or reps <= 0:
                continue
            # Epley formula: 1RM = weight * (1 + reps/30)
            estimated_1rm = weight * (1 + reps / 30)
            existing = exercise_best.get(log.exercise_id)
            if existing is None or estimated_1rm > existing["estimated_1rm"]:
                exercise_best[log.exercise_id] = {
                    "best_weight": weight,
                    "best_reps": reps,
                    "estimated_1rm": round(estimated_1rm, 1),
                }

    if not exercise_best:
        return []

    # Get exercise names
    exercise_ids = list(exercise_best.keys())
    exercises_result = await session.execute(
        select(Exercise.id, Exercise.name).where(Exercise.id.in_(exercise_ids))
    )
    exercise_names = {e.id: e.name for e in exercises_result.all()}

    # Get user body weight for strength levels
    latest_weight = await session.execute(
        select(WeightLog.weight_lbs)
        .where(WeightLog.user_id == user.id, WeightLog.weight_lbs.isnot(None))
        .order_by(WeightLog.date.desc())
        .limit(1)
    )
    body_weight = latest_weight.scalar_one_or_none()

    results = []
    for ex_id, data in sorted(
        exercise_best.items(), key=lambda x: x[1]["estimated_1rm"], reverse=True
    ):
        name = exercise_names.get(ex_id, f"Exercise {ex_id}")
        level = _strength_level(data["estimated_1rm"], body_weight)
        results.append(
            StrengthScore(
                exercise_id=ex_id,
                exercise_name=name,
                best_weight=data["best_weight"],
                best_reps=data["best_reps"],
                estimated_1rm=data["estimated_1rm"],
                level=level,
            )
        )

    return results


def _strength_level(estimated_1rm: float, body_weight: float | None) -> str:
    """Classify strength level based on 1RM to bodyweight ratio."""
    if not body_weight or body_weight <= 0:
        return "unknown"
    ratio = estimated_1rm / body_weight
    if ratio >= 2.0:
        return "elite"
    elif ratio >= 1.5:
        return "advanced"
    elif ratio >= 1.0:
        return "intermediate"
    else:
        return "beginner"


@router.get("/weekly")
async def get_weekly_progress(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
) -> list[WeeklyProgress]:
    """Get weekly progress toward targets."""
    now = datetime.now(UTC)
    # Start of current week (Monday)
    start_of_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )

    # Get user preferences for targets
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    prefs = profile.preferences if profile else {}

    target_workouts = prefs.get("days_per_week", 4)
    target_volume = prefs.get("weekly_volume_target", 100)  # total sets
    target_cardio = prefs.get("weekly_cardio_minutes", 60)

    # Count workouts this week
    workout_count = (
        await session.execute(
            select(func.count())
            .select_from(WorkoutSession)
            .where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.completed_date >= start_of_week,
            )
        )
    ).scalar() or 0

    # Count total sets this week
    week_session_ids_result = await session.execute(
        select(WorkoutSession.id).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_date >= start_of_week,
        )
    )
    week_session_ids = [s.id for s in week_session_ids_result.all()]

    total_sets = 0
    total_cardio = 0
    if week_session_ids:
        logs_result = await session.execute(
            select(ExerciseLog.sets_data).where(
                ExerciseLog.workout_session_id.in_(week_session_ids)
            )
        )
        for (sets_data,) in logs_result.all():
            total_sets += len(sets_data) if sets_data else 0

        # Sum workout durations as cardio proxy
        duration_result = await session.execute(
            select(func.sum(WorkoutSession.duration_minutes)).where(
                WorkoutSession.id.in_(week_session_ids)
            )
        )
        total_cardio = duration_result.scalar() or 0

    def pct(actual: float, target: float) -> float:
        return min(100, round((actual / target) * 100, 1)) if target > 0 else 0

    return [
        WeeklyProgress(
            metric="workouts",
            label="Workouts",
            target=target_workouts,
            actual=workout_count,
            pct=pct(workout_count, target_workouts),
        ),
        WeeklyProgress(
            metric="volume",
            label="Total Sets",
            target=target_volume,
            actual=total_sets,
            pct=pct(total_sets, target_volume),
        ),
        WeeklyProgress(
            metric="duration",
            label="Active Minutes",
            target=target_cardio,
            actual=total_cardio,
            pct=pct(total_cardio, target_cardio),
        ),
    ]


@router.get("/calendar")
async def get_calendar(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    year: int = Query(default=None),
    month: int = Query(default=None),
) -> list[CalendarDay]:
    """Get workout calendar for a given month."""
    now = datetime.now(UTC)
    year = year or now.year
    month = month or now.month

    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    # Get all workout sessions in this month
    result = await session.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_date >= start,
            WorkoutSession.completed_date < end,
        )
        .order_by(WorkoutSession.completed_date)
    )
    workouts = result.scalars().all()

    # Group by date
    day_data: dict[str, list] = defaultdict(list)
    for w in workouts:
        if w.completed_date:
            date_str = w.completed_date.strftime("%Y-%m-%d")
            day_data[date_str].append(w)

    # Get exercise names for session IDs
    session_ids = [w.id for w in workouts]
    exercise_names_map: dict[int, list[str]] = defaultdict(list)
    if session_ids:
        logs_result = await session.execute(
            select(ExerciseLog.workout_session_id, Exercise.name)
            .join(Exercise, ExerciseLog.exercise_id == Exercise.id)
            .where(ExerciseLog.workout_session_id.in_(session_ids))
        )
        for ws_id, ex_name in logs_result.all():
            exercise_names_map[ws_id].append(ex_name)

    # Build calendar days for the entire month
    days = []
    current = start
    while current < end:
        date_str = current.strftime("%Y-%m-%d")
        day_workouts = day_data.get(date_str, [])
        exercises = []
        total_duration = 0
        for w in day_workouts:
            exercises.extend(exercise_names_map.get(w.id, []))
            total_duration += w.duration_minutes or 0

        days.append(
            CalendarDay(
                date=date_str,
                has_workout=len(day_workouts) > 0,
                workout_count=len(day_workouts),
                total_duration=total_duration if total_duration > 0 else None,
                exercises=list(dict.fromkeys(exercises)),  # dedupe preserving order
            )
        )
        current += timedelta(days=1)

    return days


@router.get("/macros")
async def get_daily_macros(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    days: int = Query(default=30, ge=1, le=365),
):
    """Get daily macro totals for charting."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    cutoff = cutoff.replace(tzinfo=None)

    result = await session.execute(
        select(MealLog)
        .where(MealLog.user_id == user.id, MealLog.date >= cutoff)
        .order_by(MealLog.date)
    )
    meals = result.scalars().all()

    daily: dict[str, dict] = defaultdict(
        lambda: {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    )
    for meal in meals:
        date_str = meal.date.strftime("%Y-%m-%d")
        daily[date_str]["calories"] += meal.calories or 0
        daily[date_str]["protein_g"] += meal.protein_g or 0
        daily[date_str]["carbs_g"] += meal.carbs_g or 0
        daily[date_str]["fat_g"] += meal.fat_g or 0

    return [{"date": k, **v} for k, v in sorted(daily.items())]


@router.get("/volume")
async def get_volume_history(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    days: int = Query(default=90, ge=1, le=365),
):
    """Get training volume over time for charting."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    cutoff = cutoff.replace(tzinfo=None)

    result = await session.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_date >= cutoff,
        )
        .order_by(WorkoutSession.completed_date)
    )
    workouts = result.scalars().all()

    if not workouts:
        return []

    session_ids = [w.id for w in workouts]
    session_dates = {
        w.id: w.completed_date.strftime("%Y-%m-%d") if w.completed_date else None
        for w in workouts
    }

    logs_result = await session.execute(
        select(ExerciseLog).where(ExerciseLog.workout_session_id.in_(session_ids))
    )
    all_logs = logs_result.scalars().all()

    daily_volume: dict[str, dict] = defaultdict(
        lambda: {"total_sets": 0, "total_reps": 0, "total_weight": 0}
    )
    for log in all_logs:
        date_str = session_dates.get(log.workout_session_id)
        if not date_str:
            continue
        for set_data in log.sets_data or []:
            daily_volume[date_str]["total_sets"] += 1
            reps = set_data.get("reps", 0) or 0
            weight = set_data.get("weight", 0) or 0
            daily_volume[date_str]["total_reps"] += reps
            daily_volume[date_str]["total_weight"] += weight * reps

    return [{"date": k, **v} for k, v in sorted(daily_volume.items())]


@router.get("/preferences")
async def get_training_preferences(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Get current training preferences."""
    profile = (
        await session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    ).scalar_one_or_none()

    if not profile:
        return {
            "training_goal": None,
            "training_split": None,
            "days_per_week": 4,
            "session_duration_minutes": 60,
            "weekly_volume_target": 100,
            "weekly_cardio_minutes": 60,
            "experience_level": None,
            "equipment_access": [],
        }

    prefs = profile.preferences or {}
    return {
        "training_goal": prefs.get("training_goal", prefs.get("goal")),
        "training_split": prefs.get("training_split"),
        "days_per_week": prefs.get("days_per_week", 4),
        "session_duration_minutes": prefs.get("session_duration_minutes", 60),
        "weekly_volume_target": prefs.get("weekly_volume_target", 100),
        "weekly_cardio_minutes": prefs.get("weekly_cardio_minutes", 60),
        "experience_level": profile.experience_level,
        "equipment_access": profile.equipment_access or [],
    }


@router.put("/preferences")
async def update_training_preferences(
    prefs_data: TrainingPreferencesUpdate,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
):
    """Update training preferences (stored in UserProfile.preferences)."""
    profile = (
        await session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    ).scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=user.id, preferences={})
        session.add(profile)

    current_prefs = dict(profile.preferences or {})
    update_data = prefs_data.model_dump(exclude_none=True)
    current_prefs.update(update_data)
    profile.preferences = current_prefs
    profile.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(profile)

    return {"ok": True, "preferences": profile.preferences}


def _best_1rm_from_sets(sets_data: list[dict]) -> tuple[float, float, int] | None:
    """Return (estimated_1rm, weight, reps) for the best set, or None."""
    best = None
    for s in sets_data or []:
        weight = s.get("weight")
        reps = s.get("reps")
        if not weight or not reps or weight <= 0 or reps <= 0:
            continue
        e1rm = weight * (1 + reps / 30)
        if best is None or e1rm > best[0]:
            best = (e1rm, weight, reps)
    return best


async def _compute_prs(
    session: DatabaseSession,
    user: User,
    days: int,
    target_session_id: int | None = None,
) -> list[PersonalRecord]:
    """Compute personal records. If target_session_id is given, only return PRs from that session."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    cutoff = cutoff.replace(tzinfo=None)

    # Get all workout sessions chronologically
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.completed_date)
    )
    all_sessions = result.scalars().all()

    if not all_sessions:
        return []

    session_ids = [ws.id for ws in all_sessions]
    session_dates = {
        ws.id: ws.completed_date.strftime("%Y-%m-%d") if ws.completed_date else ""
        for ws in all_sessions
    }

    # Get all exercise logs
    logs_result = await session.execute(
        select(ExerciseLog).where(ExerciseLog.workout_session_id.in_(session_ids))
    )
    all_logs = logs_result.scalars().all()

    # Group logs by session
    session_logs: dict[int, list] = {}
    for log in all_logs:
        session_logs.setdefault(log.workout_session_id, []).append(log)

    # Get exercise names
    exercise_ids = list({log.exercise_id for log in all_logs})
    if not exercise_ids:
        return []
    exercises_result = await session.execute(
        select(Exercise.id, Exercise.name).where(Exercise.id.in_(exercise_ids))
    )
    exercise_names = {e.id: e.name for e in exercises_result.all()}

    # Walk through sessions chronologically, tracking running best 1RM per exercise
    running_best: dict[int, float] = {}  # exercise_id -> best 1RM so far
    prs: list[PersonalRecord] = []

    for ws in all_sessions:
        logs = session_logs.get(ws.id, [])
        for log in logs:
            best = _best_1rm_from_sets(log.sets_data)
            if best is None:
                continue
            e1rm, weight, reps = best
            prev_best = running_best.get(log.exercise_id)

            if prev_best is None or e1rm > prev_best:
                # This is a PR — only include if in date range / target session
                completed = ws.completed_date
                if completed and completed.tzinfo is not None:
                    completed = completed.replace(tzinfo=None)
                in_range = completed and completed >= cutoff
                is_target = target_session_id is not None and ws.id == target_session_id

                if (target_session_id is None and in_range) or is_target:
                    improvement = None
                    if prev_best and prev_best > 0:
                        improvement = round((e1rm - prev_best) / prev_best * 100, 1)
                    prs.append(
                        PersonalRecord(
                            exercise_id=log.exercise_id,
                            exercise_name=exercise_names.get(
                                log.exercise_id, f"Exercise {log.exercise_id}"
                            ),
                            pr_date=session_dates.get(ws.id, ""),
                            weight=weight,
                            reps=reps,
                            estimated_1rm=round(e1rm, 1),
                            previous_1rm=round(prev_best, 1) if prev_best else None,
                            improvement_pct=improvement,
                        )
                    )
                running_best[log.exercise_id] = e1rm

    return prs


@router.get("/prs")
async def get_personal_records(
    session: DatabaseSession,
    user: User = Depends(current_active_user),
    days: int = Query(default=90, ge=1, le=365),
) -> list[PersonalRecord]:
    """Get personal records achieved within the given date range."""
    return await _compute_prs(session, user, days)


@router.get("/prs/session/{session_id}")
async def get_session_prs(
    session_id: int,
    session: DatabaseSession,
    user: User = Depends(current_active_user),
) -> list[PersonalRecord]:
    """Get personal records achieved in a specific workout session."""
    return await _compute_prs(session, user, days=3650, target_session_id=session_id)
