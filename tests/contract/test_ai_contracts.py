"""Contract tests for AI endpoints (all mocked)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.ai import MealPlanOutput, WorkoutPlanOutput
from src.services.nl_parser import ParsedMeal, ParsedWorkout, ParsedExercise, ParsedSet


@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_workout_plan_shape(
    authenticated_client, sample_workout_plan_request, mock_ai_response_workout
):
    """POST /api/ai/generate-workout-plan returns plan shape."""
    mock_result = AsyncMock()
    mock_result.data = WorkoutPlanOutput(**mock_ai_response_workout)
    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("src.services.ai.get_planning_agent", return_value=mock_agent):
        response = await authenticated_client.post(
            "/api/ai/generate-workout-plan",
            json=sample_workout_plan_request,
        )

    assert response.status_code == 200
    data = response.json()
    assert "weeks" in data
    assert isinstance(data["weeks"], int)
    assert "phases" in data
    assert isinstance(data["phases"], list)
    assert "rationale" in data
    assert isinstance(data["rationale"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_nutrition_plan_shape(
    authenticated_client, sample_nutrition_plan_request, mock_ai_response_nutrition
):
    """POST /api/ai/generate-nutrition-plan returns nutrition shape."""
    mock_result = AsyncMock()
    mock_result.data = MealPlanOutput(**mock_ai_response_nutrition)
    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("src.services.ai.get_nutrition_agent", return_value=mock_agent):
        response = await authenticated_client.post(
            "/api/ai/generate-nutrition-plan",
            json=sample_nutrition_plan_request,
        )

    assert response.status_code == 200
    data = response.json()
    assert "daily_protein_g" in data
    assert isinstance(data["daily_protein_g"], int)
    assert "daily_calories" in data
    assert isinstance(data["daily_calories"], int)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_coach_response_shape(authenticated_client):
    """POST /api/ai/coach returns answer string."""
    mock_result = AsyncMock()
    mock_result.data = "You should increase protein intake to support recovery."
    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("src.services.ai.get_coaching_agent", return_value=mock_agent):
        response = await authenticated_client.post(
            "/api/ai/coach",
            json={"question": "How much protein should I eat?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_parse_workout_shape(authenticated_client):
    """POST /api/ai/parse-workout returns structured parse result."""
    mock_parsed = ParsedWorkout(
        exercises=[
            ParsedExercise(
                name="Bench Press",
                sets=[ParsedSet(reps=5, weight_lbs=225)],
            )
        ],
        duration_minutes=45,
    )
    mock_result = AsyncMock()
    mock_result.data = mock_parsed
    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("src.services.nl_parser.get_workout_parser", return_value=mock_agent):
        response = await authenticated_client.post(
            "/api/ai/parse-workout",
            json={"text": "Bench press 225x5x3"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "exercises" in data
    assert isinstance(data["exercises"], list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_parse_meal_shape(authenticated_client):
    """POST /api/ai/parse-meal returns structured parse result."""
    mock_parsed = ParsedMeal(
        meal_type="lunch",
        description="Chicken breast with rice",
        protein_g=50,
        carbs_g=45,
        calories=440,
    )
    mock_result = AsyncMock()
    mock_result.data = mock_parsed
    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("src.services.nl_parser.get_meal_parser", return_value=mock_agent):
        response = await authenticated_client.post(
            "/api/ai/parse-meal",
            json={"text": "Chicken breast 8oz with a cup of rice"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "description" in data
    assert isinstance(data["description"], str)
