"""Tests for analytics API endpoints: recovery, strength, weekly, calendar, macros, volume, preferences"""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Exercise, ExerciseLog, MealLog, User, UserProfile, WorkoutSession


@pytest_asyncio.fixture
async def exercises(test_db: AsyncSession) -> list[Exercise]:
    """Create test exercises for analytics tests."""
    exercises = [
        Exercise(
            id=1,
            name="Bench Press",
            category="strength",
            equipment="barbell",
            difficulty="intermediate",
            primary_muscles=["chest"],
            secondary_muscles=["triceps", "shoulders"],
        ),
        Exercise(
            id=2,
            name="Squat",
            category="strength",
            equipment="barbell",
            difficulty="intermediate",
            primary_muscles=["quadriceps"],
            secondary_muscles=["glutes", "hamstrings"],
        ),
        Exercise(
            id=3,
            name="Deadlift",
            category="strength",
            equipment="barbell",
            difficulty="intermediate",
            primary_muscles=["lower back", "hamstrings"],
            secondary_muscles=["glutes", "forearms"],
        ),
    ]
    for ex in exercises:
        test_db.add(ex)
    await test_db.commit()
    return exercises


@pytest_asyncio.fixture
async def workout_with_logs(
    test_db: AsyncSession,
    test_user: User,
    exercises: list[Exercise],
) -> WorkoutSession:
    """Create a workout session with exercise logs."""
    now = datetime.now(UTC)
    workout = WorkoutSession(
        user_id=test_user.id,
        completed_date=now,
        duration_minutes=60,
        overall_rpe=7,
    )
    test_db.add(workout)
    await test_db.flush()

    logs = [
        ExerciseLog(
            workout_session_id=workout.id,
            exercise_id=1,
            sets_data=[
                {"weight": 135, "reps": 10},
                {"weight": 155, "reps": 8},
                {"weight": 175, "reps": 6},
            ],
        ),
        ExerciseLog(
            workout_session_id=workout.id,
            exercise_id=2,
            sets_data=[
                {"weight": 185, "reps": 8},
                {"weight": 205, "reps": 6},
            ],
        ),
    ]
    for log in logs:
        test_db.add(log)
    await test_db.commit()
    return workout


@pytest_asyncio.fixture
async def weight_log(test_db: AsyncSession, test_user: User):
    """Create a weight log for strength level calculation."""
    from src.models import WeightLog

    wl = WeightLog(
        user_id=test_user.id,
        date=datetime.now(UTC),
        weight_lbs=180.0,
    )
    test_db.add(wl)
    await test_db.commit()
    return wl


@pytest_asyncio.fixture
async def meals(test_db: AsyncSession, test_user: User) -> list[MealLog]:
    """Create test meals for macro tracking."""
    now = datetime.now(UTC)
    meals = [
        MealLog(
            user_id=test_user.id,
            date=now,
            meal_type="breakfast",
            description="Eggs and toast",
            protein_g=30.0,
            carbs_g=40.0,
            fat_g=15.0,
            calories=420,
        ),
        MealLog(
            user_id=test_user.id,
            date=now,
            meal_type="lunch",
            description="Chicken and rice",
            protein_g=45.0,
            carbs_g=60.0,
            fat_g=12.0,
            calories=540,
        ),
    ]
    for m in meals:
        test_db.add(m)
    await test_db.commit()
    return meals


class TestRecovery:
    @pytest.mark.asyncio
    async def test_recovery_empty(self, authenticated_client: AsyncClient):
        """No workouts = empty recovery list."""
        resp = await authenticated_client.get("/api/analytics/recovery")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_recovery_with_workout(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """Recent workout shows muscles recovering."""
        resp = await authenticated_client.get("/api/analytics/recovery")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        muscles = {d["muscle"] for d in data}
        assert "chest" in muscles
        assert "quadriceps" in muscles
        for item in data:
            assert item["status"] == "recovering"
            assert item["recovery_pct"] < 100
            assert item["hours_since"] is not None

    @pytest.mark.asyncio
    async def test_recovery_requires_auth(self, test_client: AsyncClient, test_user):
        """Recovery endpoint requires authentication."""
        resp = await test_client.get("/api/analytics/recovery")
        assert resp.status_code == 401


class TestStrength:
    @pytest.mark.asyncio
    async def test_strength_empty(self, authenticated_client: AsyncClient):
        """No exercise logs = empty strength scores."""
        resp = await authenticated_client.get("/api/analytics/strength")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_strength_with_logs(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
        weight_log,
    ):
        """Exercise logs produce strength scores with Epley 1RM."""
        resp = await authenticated_client.get("/api/analytics/strength")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # bench + squat

        # Verify 1RM calculation for bench: 175 * (1 + 6/30) = 210
        bench = next(d for d in data if d["exercise_name"] == "Bench Press")
        assert bench["best_weight"] == 175
        assert bench["best_reps"] == 6
        assert bench["estimated_1rm"] == 210.0
        # 210 / 180 = 1.17 -> intermediate
        assert bench["level"] == "intermediate"

    @pytest.mark.asyncio
    async def test_strength_without_bodyweight(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """Without bodyweight, strength level is unknown."""
        resp = await authenticated_client.get("/api/analytics/strength")
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["level"] == "unknown"


class TestWeekly:
    @pytest.mark.asyncio
    async def test_weekly_empty(self, authenticated_client: AsyncClient):
        """No data = zero actual values."""
        resp = await authenticated_client.get("/api/analytics/weekly")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        metrics = {d["metric"] for d in data}
        assert metrics == {"workouts", "volume", "duration"}
        for item in data:
            assert item["actual"] == 0
            assert item["pct"] == 0

    @pytest.mark.asyncio
    async def test_weekly_with_data(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
        test_user_profile: UserProfile,
    ):
        """Workout this week shows progress toward targets."""
        resp = await authenticated_client.get("/api/analytics/weekly")
        assert resp.status_code == 200
        data = resp.json()
        workouts = next(d for d in data if d["metric"] == "workouts")
        assert workouts["actual"] == 1
        assert workouts["pct"] > 0

        volume = next(d for d in data if d["metric"] == "volume")
        assert volume["actual"] == 5  # 3 bench sets + 2 squat sets


class TestCalendar:
    @pytest.mark.asyncio
    async def test_calendar_current_month(self, authenticated_client: AsyncClient):
        """Calendar returns days for the current month."""
        now = datetime.now(UTC)
        resp = await authenticated_client.get(
            f"/api/analytics/calendar?year={now.year}&month={now.month}"
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should have correct number of days for the month
        import calendar

        expected_days = calendar.monthrange(now.year, now.month)[1]
        assert len(data) == expected_days

    @pytest.mark.asyncio
    async def test_calendar_with_workout(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """Calendar shows workout data on the correct day."""
        now = datetime.now(UTC)
        resp = await authenticated_client.get(
            f"/api/analytics/calendar?year={now.year}&month={now.month}"
        )
        assert resp.status_code == 200
        data = resp.json()

        today_str = now.strftime("%Y-%m-%d")
        today_entry = next((d for d in data if d["date"] == today_str), None)
        assert today_entry is not None
        assert today_entry["has_workout"] is True
        assert today_entry["workout_count"] == 1
        assert today_entry["total_duration"] == 60

    @pytest.mark.asyncio
    async def test_calendar_default_params(self, authenticated_client: AsyncClient):
        """Calendar defaults to current month if no params."""
        resp = await authenticated_client.get("/api/analytics/calendar")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        # First day should be the 1st of current month
        now = datetime.now(UTC)
        expected_first = f"{now.year}-{now.month:02d}-01"
        assert data[0]["date"] == expected_first


class TestMacros:
    @pytest.mark.asyncio
    async def test_macros_empty(self, authenticated_client: AsyncClient):
        """No meals = empty macros."""
        resp = await authenticated_client.get("/api/analytics/macros")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_macros_with_meals(
        self,
        authenticated_client: AsyncClient,
        meals: list[MealLog],
    ):
        """Meals aggregate into daily macro totals."""
        resp = await authenticated_client.get("/api/analytics/macros?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1  # both meals on same day
        day = data[0]
        assert day["protein_g"] == 75.0  # 30 + 45
        assert day["carbs_g"] == 100.0  # 40 + 60
        assert day["fat_g"] == 27.0  # 15 + 12
        assert day["calories"] == 960  # 420 + 540


class TestVolume:
    @pytest.mark.asyncio
    async def test_volume_empty(self, authenticated_client: AsyncClient):
        """No workouts = empty volume."""
        resp = await authenticated_client.get("/api/analytics/volume")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_volume_with_data(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """Volume aggregates set data correctly."""
        resp = await authenticated_client.get("/api/analytics/volume?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        day = data[0]
        assert day["total_sets"] == 5  # 3 bench + 2 squat
        # total_reps = 10+8+6+8+6 = 38
        assert day["total_reps"] == 38
        # total_weight = 135*10 + 155*8 + 175*6 + 185*8 + 205*6
        # = 1350 + 1240 + 1050 + 1480 + 1230 = 6350
        assert day["total_weight"] == 6350


class TestPreferences:
    @pytest.mark.asyncio
    async def test_get_defaults(self, authenticated_client: AsyncClient):
        """Without profile, returns defaults."""
        resp = await authenticated_client.get("/api/analytics/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["days_per_week"] == 4
        assert data["session_duration_minutes"] == 60

    @pytest.mark.asyncio
    async def test_get_with_profile(
        self,
        authenticated_client: AsyncClient,
        test_user_profile: UserProfile,
    ):
        """With profile, returns stored preferences."""
        resp = await authenticated_client.get("/api/analytics/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["training_goal"] == "muscle_gain"
        assert data["experience_level"] == "intermediate"

    @pytest.mark.asyncio
    async def test_update_preferences(self, authenticated_client: AsyncClient):
        """PUT preferences creates profile if missing and stores data."""
        resp = await authenticated_client.put(
            "/api/analytics/preferences",
            json={
                "training_goal": "strength",
                "days_per_week": 5,
                "session_duration_minutes": 90,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["preferences"]["training_goal"] == "strength"
        assert data["preferences"]["days_per_week"] == 5

    @pytest.mark.asyncio
    async def test_update_merges_preferences(
        self,
        authenticated_client: AsyncClient,
        test_user_profile: UserProfile,
    ):
        """PUT merges new values with existing preferences."""
        # Update just one field
        resp = await authenticated_client.put(
            "/api/analytics/preferences",
            json={"training_split": "push_pull_legs"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Original goal should still be there
        assert data["preferences"]["goal"] == "muscle_gain"
        assert data["preferences"]["training_split"] == "push_pull_legs"

    @pytest.mark.asyncio
    async def test_preferences_require_auth(self, test_client: AsyncClient, test_user):
        """Preferences endpoints require authentication."""
        resp = await test_client.get("/api/analytics/preferences")
        assert resp.status_code == 401
        resp = await test_client.put(
            "/api/analytics/preferences",
            json={"days_per_week": 3},
        )
        assert resp.status_code == 401


class TestPersonalRecords:
    @pytest.mark.asyncio
    async def test_prs_empty(self, authenticated_client: AsyncClient):
        """No workout data = empty PRs."""
        resp = await authenticated_client.get("/api/analytics/prs")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_prs_first_session_counts(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """First workout's exercises are all PRs (no prior data)."""
        resp = await authenticated_client.get("/api/analytics/prs?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # bench + squat
        names = {d["exercise_name"] for d in data}
        assert "Bench Press" in names
        assert "Squat" in names
        # First PRs have no previous_1rm
        for pr in data:
            assert pr["previous_1rm"] is None

    @pytest.mark.asyncio
    async def test_prs_improvement_detected(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        test_user: User,
        exercises: list[Exercise],
    ):
        """A stronger second session detects improvement over the first."""
        now = datetime.now(UTC)
        # First session (weaker)
        ws1 = WorkoutSession(
            user_id=test_user.id,
            completed_date=now - timedelta(days=7),
            duration_minutes=45,
        )
        test_db.add(ws1)
        await test_db.flush()
        test_db.add(
            ExerciseLog(
                workout_session_id=ws1.id,
                exercise_id=1,
                sets_data=[{"weight": 135, "reps": 8}],
            )
        )
        # Second session (stronger)
        ws2 = WorkoutSession(
            user_id=test_user.id,
            completed_date=now,
            duration_minutes=45,
        )
        test_db.add(ws2)
        await test_db.flush()
        test_db.add(
            ExerciseLog(
                workout_session_id=ws2.id,
                exercise_id=1,
                sets_data=[{"weight": 155, "reps": 8}],
            )
        )
        await test_db.commit()

        resp = await authenticated_client.get("/api/analytics/prs?days=90")
        assert resp.status_code == 200
        data = resp.json()
        # Should have 2 PRs: first session (no prev) + improvement
        bench_prs = [d for d in data if d["exercise_name"] == "Bench Press"]
        assert len(bench_prs) == 2
        improved = [p for p in bench_prs if p["improvement_pct"] is not None]
        assert len(improved) == 1
        assert improved[0]["improvement_pct"] > 0

    @pytest.mark.asyncio
    async def test_session_prs(
        self,
        authenticated_client: AsyncClient,
        workout_with_logs: WorkoutSession,
    ):
        """Session PR endpoint returns PRs for a specific session."""
        resp = await authenticated_client.get(
            f"/api/analytics/prs/session/{workout_with_logs.id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # first session = all PRs

    @pytest.mark.asyncio
    async def test_prs_require_auth(self, test_client: AsyncClient, test_user):
        """PR endpoints require authentication."""
        resp = await test_client.get("/api/analytics/prs")
        assert resp.status_code == 401


class TestWorkoutWithExerciseLogs:
    @pytest.mark.asyncio
    async def test_log_workout_with_exercises(
        self,
        authenticated_client: AsyncClient,
        exercises: list[Exercise],
    ):
        """Workout creation includes exercise logs."""
        resp = await authenticated_client.post(
            "/api/workouts",
            json={
                "completed_date": datetime.now(UTC).isoformat(),
                "duration_minutes": 45,
                "overall_rpe": 7,
                "exercise_logs": [
                    {
                        "exercise_id": 1,
                        "sets_data": [
                            {"weight": 135, "reps": 10},
                            {"weight": 155, "reps": 8},
                        ],
                        "notes": "Felt strong",
                    },
                    {
                        "exercise_id": 2,
                        "sets_data": [
                            {"weight": 185, "reps": 8},
                        ],
                    },
                ],
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_log_workout_without_exercises(
        self,
        authenticated_client: AsyncClient,
    ):
        """Workout creation works without exercise logs (backward compat)."""
        resp = await authenticated_client.post(
            "/api/workouts",
            json={
                "completed_date": datetime.now(UTC).isoformat(),
                "duration_minutes": 30,
                "notes": "Quick cardio",
            },
        )
        assert resp.status_code == 200
