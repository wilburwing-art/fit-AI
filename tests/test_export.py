"""Tests for data export endpoints (JSON and CSV)"""

from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MealLog, User, WeightLog, WorkoutSession


@pytest_asyncio.fixture
async def export_data(test_db: AsyncSession, test_user: User):
    """Create sample data for export tests."""
    now = datetime.now(UTC).replace(tzinfo=None)

    wl = WeightLog(user_id=test_user.id, date=now, weight_lbs=180.0)
    ml = MealLog(
        user_id=test_user.id,
        date=now,
        meal_type="lunch",
        description="Chicken",
        protein_g=40.0,
        carbs_g=50.0,
        fat_g=10.0,
        calories=450,
    )
    ws = WorkoutSession(
        user_id=test_user.id,
        completed_date=now,
        duration_minutes=60,
        overall_rpe=7,
    )

    test_db.add_all([wl, ml, ws])
    await test_db.commit()
    return {"weight": wl, "meal": ml, "workout": ws}


class TestExportJSON:
    @pytest.mark.asyncio
    async def test_json_empty(self, authenticated_client: AsyncClient):
        """JSON export with no data returns empty lists."""
        resp = await authenticated_client.get("/api/export/json?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert data["weight_logs"] == []
        assert data["meal_logs"] == []
        assert data["workout_sessions"] == []
        assert "Content-Disposition" in resp.headers
        assert "attachment" in resp.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_json_with_data(
        self, authenticated_client: AsyncClient, export_data
    ):
        """JSON export includes all data types."""
        resp = await authenticated_client.get("/api/export/json?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["weight_logs"]) == 1
        assert data["weight_logs"][0]["weight_lbs"] == 180.0
        assert len(data["meal_logs"]) == 1
        assert data["meal_logs"][0]["calories"] == 450
        assert len(data["workout_sessions"]) == 1
        assert data["workout_sessions"][0]["duration_minutes"] == 60


class TestExportCSV:
    @pytest.mark.asyncio
    async def test_csv_format(self, authenticated_client: AsyncClient, export_data):
        """CSV export returns valid CSV with section headers."""
        resp = await authenticated_client.get("/api/export/csv?days=90")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["Content-Disposition"]

        body = resp.text
        assert "# Weight Logs" in body
        assert "# Meal Logs" in body
        assert "# Workout Sessions" in body
        assert "180.0" in body


class TestExportValidation:
    @pytest.mark.asyncio
    async def test_days_validation(self, authenticated_client: AsyncClient):
        """Days parameter is validated (1-365)."""
        resp = await authenticated_client.get("/api/export/json?days=0")
        assert resp.status_code == 422

        resp = await authenticated_client.get("/api/export/json?days=500")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_auth_required(self, test_client: AsyncClient, test_user):
        """Export endpoints require authentication."""
        resp = await test_client.get("/api/export/json")
        assert resp.status_code == 401

        resp = await test_client.get("/api/export/csv")
        assert resp.status_code == 401
