"""E2E tests for the workouts page (timer, exercise form)."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login_via_browser

pytestmark = pytest.mark.e2e


def test_workout_page_has_timer(page: Page, live_server: str, registered_user: dict):
    """Verify Start, Reset, and rest preset buttons are visible."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    page.goto(f"{live_server}/workouts")
    expect(page.locator("button", has_text="Start")).to_be_visible()
    expect(page.locator("button", has_text="Reset")).to_be_visible()
    expect(page.locator("button", has_text="1:00")).to_be_visible()
    expect(page.locator("button", has_text="1:30")).to_be_visible()
    expect(page.locator("button", has_text="2:00")).to_be_visible()
    expect(page.locator("button", has_text="3:00")).to_be_visible()


def test_add_exercise_shows_form(page: Page, live_server: str, registered_user: dict):
    """Click + Add Exercise, verify search input appears."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    page.goto(f"{live_server}/workouts")
    add_btn = page.locator("button", has_text="+ Add Exercise")
    add_btn.click()
    search_input = page.locator('input[placeholder="Search exercise..."]')
    expect(search_input).to_be_visible()
    weight_input = page.locator('input[placeholder="lbs"]')
    expect(weight_input).to_be_visible()
    reps_input = page.locator('input[placeholder="reps"]')
    expect(reps_input).to_be_visible()


def test_timer_starts_and_counts(page: Page, live_server: str, registered_user: dict):
    """Click Start, wait, verify display is not 00:00."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    page.goto(f"{live_server}/workouts")
    start_btn = page.locator("button", has_text="Start")
    start_btn.click()
    page.wait_for_timeout(1500)
    timer_display = page.locator(".font-mono.font-bold").first
    text = timer_display.text_content()
    assert text != "00:00", f"Timer should have advanced from 00:00, got {text}"
