"""Contract tests for data logging endpoints."""

from datetime import UTC, datetime

import pytest

from src.schemas import MealLogRead, WeightLogRead, WorkoutSessionRead
from tests.contract.conftest import (
    assert_error_response,
    assert_list_matches_schema,
    assert_matches_schema,
)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_weight_response_shape(authenticated_client):
    """POST /api/weight returns WeightLogRead shape."""
    response = await authenticated_client.post(
        "/api/weight",
        json={
            "date": datetime.now(UTC).isoformat(),
            "weight_lbs": 185.0,
            "body_fat_pct": 15.0,
            "measurements": {},
        },
    )
    assert response.status_code == 200
    assert_matches_schema(response.json(), WeightLogRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_weight_response_shape(authenticated_client):
    """GET /api/weight returns list of WeightLogRead."""
    response = await authenticated_client.get("/api/weight")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert_list_matches_schema(data, WeightLogRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_weight_invalid(authenticated_client):
    """POST /api/weight with invalid data returns 422."""
    response = await authenticated_client.post(
        "/api/weight",
        json={
            "date": datetime.now(UTC).isoformat(),
            "weight_lbs": 10000,
        },
    )
    assert_error_response(response, 422)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_meal_response_shape(authenticated_client):
    """POST /api/meals returns MealLogRead shape."""
    response = await authenticated_client.post(
        "/api/meals",
        json={
            "date": datetime.now(UTC).isoformat(),
            "meal_type": "lunch",
            "description": "Chicken and rice",
            "protein_g": 40.0,
            "carbs_g": 50.0,
            "fat_g": 10.0,
            "calories": 450,
        },
    )
    assert response.status_code == 200
    assert_matches_schema(response.json(), MealLogRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_meals_response_shape(authenticated_client):
    """GET /api/meals returns list of MealLogRead."""
    response = await authenticated_client.get("/api/meals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert_list_matches_schema(data, MealLogRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_workout_response_shape(authenticated_client):
    """POST /api/workouts returns WorkoutSessionRead shape."""
    response = await authenticated_client.post(
        "/api/workouts",
        json={
            "completed_date": datetime.now(UTC).isoformat(),
            "duration_minutes": 60,
            "overall_rpe": 7,
            "notes": "Contract test workout",
        },
    )
    assert response.status_code == 200
    assert_matches_schema(response.json(), WorkoutSessionRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_workouts_response_shape(authenticated_client):
    """GET /api/workouts returns list of WorkoutSessionRead."""
    response = await authenticated_client.get("/api/workouts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert_list_matches_schema(data, WorkoutSessionRead)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_recent_activity_response_shape(authenticated_client):
    """GET /api/recent-activity returns list."""
    response = await authenticated_client.get("/api/recent-activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
