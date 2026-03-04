"""E2E tests for navigation guards and page access."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_unauth_dashboard_redirects(page: Page, live_server: str):
    """Going to /dashboard without login redirects to /login."""
    page.goto(f"{live_server}/dashboard")
    page.wait_for_url("**/login", timeout=5000)
    assert "/login" in page.url


def test_unauth_workouts_redirects(page: Page, live_server: str):
    """Going to /workouts without login redirects to /login."""
    page.goto(f"{live_server}/workouts")
    page.wait_for_url("**/login", timeout=5000)
    assert "/login" in page.url


def test_unauth_coach_redirects(page: Page, live_server: str):
    """Going to /coach without login redirects to /login."""
    page.goto(f"{live_server}/coach")
    page.wait_for_url("**/login", timeout=5000)
    assert "/login" in page.url


def test_unauth_preferences_redirects(page: Page, live_server: str):
    """Going to /preferences without login redirects to /login."""
    page.goto(f"{live_server}/preferences")
    page.wait_for_url("**/login", timeout=5000)
    assert "/login" in page.url


def test_home_accessible_without_auth(page: Page, live_server: str):
    """Going to / works without login, shows Fit Agent text."""
    page.goto(f"{live_server}/")
    heading = page.locator("text=Fit Agent")
    expect(heading.first).to_be_visible()
