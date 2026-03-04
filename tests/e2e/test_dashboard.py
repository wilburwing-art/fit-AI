"""E2E tests for dashboard quick-log cards."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_dashboard_loads_with_cards(authenticated_page: Page):
    """Verify dashboard shows Log Weight, Log Meal, Quick Workout headings."""
    expect(authenticated_page.locator("h3", has_text="Log Weight")).to_be_visible()
    expect(authenticated_page.locator("h3", has_text="Log Meal")).to_be_visible()
    expect(authenticated_page.locator("h3", has_text="Quick Workout")).to_be_visible()


def test_log_weight_from_dashboard(authenticated_page: Page):
    """Fill weight input, submit, verify success message."""
    p = authenticated_page
    p.fill("#weight", "185")
    weight_form = p.locator('form[hx-post="/api/weight"]')
    weight_form.locator('button[type="submit"]').click()
    msg = p.locator('[x-ref="weightMsg"]')
    expect(msg).to_have_text("Logged!", timeout=5000)


def test_log_meal_from_dashboard(authenticated_page: Page):
    """Fill meal description, submit, verify success message."""
    p = authenticated_page
    meal_form = p.locator('form[hx-post="/api/meals"]')
    meal_form.locator('input[name="description"]').fill("Test chicken rice")
    meal_form.locator('button[type="submit"]').click()
    msg = p.locator('[x-ref="mealMsg"]')
    expect(msg).to_have_text("Logged!", timeout=5000)


def test_log_workout_from_dashboard(authenticated_page: Page):
    """Fill duration and RPE, submit, verify success message."""
    p = authenticated_page
    workout_form = p.locator('form[hx-post="/api/workouts"]')
    workout_form.locator('input[name="duration_minutes"]').fill("60")
    workout_form.locator('input[name="overall_rpe"]').fill("7")
    workout_form.locator('button[type="submit"]').click()
    msg = p.locator('[x-ref="workoutMsg"]')
    expect(msg).to_have_text("Logged!", timeout=5000)
