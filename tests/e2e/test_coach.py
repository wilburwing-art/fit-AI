"""E2E tests for the AI Coach page."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login_via_browser

pytestmark = pytest.mark.e2e


def test_coach_page_loads(page: Page, live_server: str, registered_user: dict):
    """Verify AI Coach heading and input are visible."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    page.goto(f"{live_server}/coach")
    heading = page.locator("h1", has_text="AI Coach")
    expect(heading).to_be_visible()
    input_field = page.locator('input[placeholder="Ask your coach..."]')
    expect(input_field).to_be_visible()


def test_send_shows_user_message(page: Page, live_server: str, registered_user: dict):
    """Type a question, click Send, verify user message bubble appears."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    page.goto(f"{live_server}/coach")
    input_field = page.locator('input[placeholder="Ask your coach..."]')
    input_field.fill("How much protein should I eat?")
    send_btn = page.locator("button", has_text="Send")
    send_btn.click()
    # The user message should appear in the chat
    user_msg = page.locator("text=How much protein should I eat?")
    expect(user_msg).to_be_visible(timeout=5000)
