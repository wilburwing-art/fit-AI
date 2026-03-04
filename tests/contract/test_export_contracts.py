"""Contract tests for export endpoints."""

import json

import pytest

from tests.contract.conftest import assert_error_response


@pytest.mark.contract
@pytest.mark.asyncio
async def test_export_json_response_shape(authenticated_client):
    """GET /api/export/json returns JSON download with expected keys."""
    response = await authenticated_client.get("/api/export/json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")

    data = json.loads(response.content)
    assert "weight_logs" in data
    assert "meal_logs" in data
    assert "workout_sessions" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_export_csv_response_shape(authenticated_client):
    """GET /api/export/csv returns CSV download."""
    response = await authenticated_client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")


@pytest.mark.contract
@pytest.mark.asyncio
async def test_export_json_invalid_days(authenticated_client):
    """GET /api/export/json with days=0 returns 422."""
    response = await authenticated_client.get("/api/export/json?days=0")
    assert_error_response(response, 422)
