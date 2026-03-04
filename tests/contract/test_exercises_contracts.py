"""Contract tests for exercise endpoints."""

import pytest

from tests.contract.conftest import assert_error_response


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_exercises_response_shape(authenticated_client):
    """GET /api/exercises returns paginated exercise list."""
    response = await authenticated_client.get("/api/exercises")
    assert response.status_code == 200
    data = response.json()
    assert "exercises" in data
    assert isinstance(data["exercises"], list)
    assert "total" in data
    assert isinstance(data["total"], int)
    assert "page" in data
    assert isinstance(data["page"], int)
    assert "per_page" in data
    assert isinstance(data["per_page"], int)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_exercise_filters_response_shape(authenticated_client):
    """GET /api/exercises/filters returns filter option lists."""
    response = await authenticated_client.get("/api/exercises/filters")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)
    assert "equipment" in data
    assert isinstance(data["equipment"], list)
    assert "difficulties" in data
    assert isinstance(data["difficulties"], list)
    assert "muscles" in data
    assert isinstance(data["muscles"], list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_exercise_not_found(authenticated_client):
    """GET /api/exercises/99999 returns 404 with detail."""
    response = await authenticated_client.get("/api/exercises/99999")
    assert_error_response(response, 404)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_exercise_preferences_list_shape(authenticated_client):
    """GET /api/exercises/preferences returns list."""
    response = await authenticated_client.get("/api/exercises/preferences")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
