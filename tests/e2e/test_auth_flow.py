"""E2E tests for authentication flows."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login_via_browser

pytestmark = pytest.mark.e2e


def test_register_and_redirect(page: Page, live_server: str):
    """Fill registration form, submit, verify redirect to /login."""
    page.goto(f"{live_server}/register")
    page.fill("#email", "e2e_register_test@test.com")
    page.fill("#password", "securePass123!")
    page.click('button[type="submit"]')
    page.wait_for_url("**/login", timeout=10000)
    assert "/login" in page.url


def test_login_and_redirect_to_dashboard(
    page: Page, live_server: str, registered_user: dict
):
    """Fill login form, submit, verify redirect to /dashboard."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    assert "/dashboard" in page.url
    heading = page.locator("h1")
    expect(heading).to_have_text("Dashboard")


def test_login_bad_credentials_shows_error(
    page: Page, live_server: str, registered_user: dict
):
    """Submit wrong password, verify error message appears."""
    page.goto(f"{live_server}/login")
    page.fill("#username", registered_user["email"])
    page.fill("#password", "wrongpassword")
    page.click('button[type="submit"]')
    msg = page.locator("#login-message")
    expect(msg).to_have_text("Invalid email or password", timeout=5000)


def test_logout(page: Page, live_server: str, registered_user: dict):
    """Login, click Logout, verify redirected away from dashboard."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    # The Logout button is in the desktop nav, controlled by Alpine
    logout_btn = page.locator("button", has_text="Logout")
    logout_btn.click()
    page.wait_for_url("**/", timeout=10000)
    # Should not be on /dashboard anymore
    assert "/dashboard" not in page.url


def test_register_link_from_login(page: Page, live_server: str):
    """Click signup link on login page, verify navigation to /register."""
    page.goto(f"{live_server}/login")
    link = page.locator("a", has_text="Don't have an account? Sign up")
    link.click()
    page.wait_for_url("**/register", timeout=5000)
    assert "/register" in page.url
