"""Contract tests for analytics endpoints."""

import pytest


@pytest.mark.contract
@pytest.mark.asyncio
async def test_recovery_response_shape(authenticated_client):
    """GET /api/analytics/recovery returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/recovery")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "muscle" in item
        assert "recovery_pct" in item
        assert "status" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_strength_response_shape(authenticated_client):
    """GET /api/analytics/strength returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/strength")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "exercise_name" in item
        assert "estimated_1rm" in item
        assert "level" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_weekly_response_shape(authenticated_client, test_user_profile):
    """GET /api/analytics/weekly returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/weekly")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "metric" in item
        assert "target" in item
        assert "actual" in item
        assert "pct" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_calendar_response_shape(authenticated_client):
    """GET /api/analytics/calendar returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/calendar")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "date" in item
        assert "has_workout" in item
        assert "workout_count" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_macros_response_shape(authenticated_client):
    """GET /api/analytics/macros returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/macros")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "date" in item
        assert "calories" in item
        assert "protein_g" in item
        assert "carbs_g" in item
        assert "fat_g" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_volume_response_shape(authenticated_client):
    """GET /api/analytics/volume returns list with expected fields."""
    response = await authenticated_client.get("/api/analytics/volume")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "date" in item
        assert "total_sets" in item
        assert "total_reps" in item
        assert "total_weight" in item


@pytest.mark.contract
@pytest.mark.asyncio
async def test_prs_response_shape(authenticated_client):
    """GET /api/analytics/prs returns list."""
    response = await authenticated_client.get("/api/analytics/prs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_preferences_get_response_shape(authenticated_client):
    """GET /api/analytics/preferences returns dict."""
    response = await authenticated_client.get("/api/analytics/preferences")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_preferences_put_response_shape(authenticated_client):
    """PUT /api/analytics/preferences returns ok and preferences."""
    response = await authenticated_client.put(
        "/api/analytics/preferences",
        json={"training_goal": "muscle_gain", "days_per_week": 4},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert data["ok"] is True
    assert "preferences" in data
