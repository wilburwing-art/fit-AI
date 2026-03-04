"""Contract tests for auth endpoints."""

import pytest

from tests.contract.conftest import assert_error_response


@pytest.mark.contract
@pytest.mark.asyncio
async def test_register_response_shape(test_client):
    """POST /auth/register returns user with expected fields."""
    response = await test_client.post(
        "/auth/register",
        json={"email": "contract_reg@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"] == "contract_reg@example.com"
    assert "is_active" in data
    assert "created_at" in data
    assert isinstance(data["is_active"], bool)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_jwt_login_response_shape(test_client, test_user):
    """POST /auth/jwt/login returns access_token and token_type."""
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert data["token_type"] == "bearer"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_cookie_login_response_shape(test_client, test_user):
    """POST /auth/cookie/login returns 204 with set-cookie header."""
    response = await test_client.post(
        "/auth/cookie/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 204
    assert "set-cookie" in response.headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_users_me_response_shape(authenticated_client):
    """GET /auth/users/me returns user with expected fields."""
    response = await authenticated_client.get("/auth/users/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "is_active" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_users_me_unauth(test_client):
    """GET /auth/users/me without auth returns 401."""
    response = await test_client.get("/auth/users/me")
    assert_error_response(response, 401)
