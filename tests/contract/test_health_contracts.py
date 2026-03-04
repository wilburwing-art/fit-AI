"""Contract tests for /health endpoint."""

import pytest


@pytest.mark.contract
@pytest.mark.asyncio
async def test_health_response_shape(test_client):
    """GET /health returns status, environment, database."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data
    assert "database" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["environment"], str)
    assert isinstance(data["database"], str)
