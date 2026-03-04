"""Tests for coaching Q&A endpoint"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MealLog, User, UserProfile, WeightLog, WorkoutSession


@pytest_asyncio.fixture
async def coaching_context_data(test_db: AsyncSession, test_user: User):
    """Create user data so coaching context is populated."""
    now = datetime.now(UTC).replace(tzinfo=None)
    profile = UserProfile(
        user_id=test_user.id,
        age=30,
        sex="M",
        experience_level="intermediate",
        preferences={"goal": "strength"},
    )
    wl = WeightLog(user_id=test_user.id, date=now, weight_lbs=180.0)
    ml = MealLog(
        user_id=test_user.id,
        date=now,
        meal_type="lunch",
        calories=600,
        protein_g=40,
    )
    ws = WorkoutSession(
        user_id=test_user.id,
        completed_date=now,
        duration_minutes=60,
        overall_rpe=7,
    )
    test_db.add_all([profile, wl, ml, ws])
    await test_db.commit()


class TestCoaching:
    @pytest.mark.asyncio
    async def test_auth_required(self, test_client: AsyncClient, test_user):
        """Coaching endpoint requires authentication."""
        resp = await test_client.post(
            "/api/ai/coach",
            json={"question": "How should I train?"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_question_validation(self, authenticated_client: AsyncClient):
        """Question must be 3-2000 chars."""
        resp = await authenticated_client.post(
            "/api/ai/coach",
            json={"question": "Hi"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @patch("src.api.ai.coaching_qa", new_callable=AsyncMock)
    async def test_returns_answer(
        self,
        mock_qa: AsyncMock,
        authenticated_client: AsyncClient,
    ):
        """Coach endpoint returns AI answer."""
        mock_qa.return_value = "You should increase your protein intake to support recovery."

        resp = await authenticated_client.post(
            "/api/ai/coach",
            json={"question": "How can I recover faster?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "protein" in data["answer"].lower()
        mock_qa.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.api.ai.coaching_qa", new_callable=AsyncMock)
    async def test_context_gathered(
        self,
        mock_qa: AsyncMock,
        authenticated_client: AsyncClient,
        coaching_context_data,
    ):
        """Coaching context includes user data."""
        mock_qa.return_value = "Based on your data, you're making progress."

        resp = await authenticated_client.post(
            "/api/ai/coach",
            json={"question": "Am I making progress?"},
        )
        assert resp.status_code == 200

        # Verify context string was passed with user data
        call_args = mock_qa.call_args
        context = call_args[1].get("user_context") or call_args[0][1]
        assert "180.0" in context  # weight
        assert "intermediate" in context  # experience level
