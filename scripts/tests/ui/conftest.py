"""Playwright fixtures for UI testing."""

import os
import pytest
from playwright.sync_api import Page, expect

# Set default timeout for assertions
expect.set_options(timeout=10000)


@pytest.fixture
def grist_url() -> str:
    """Grist instance URL."""
    return os.getenv("GRIST_URL", "http://localhost:8484")


@pytest.fixture
def grist_credentials() -> tuple[str, str]:
    """Grist login credentials."""
    email = os.getenv("GRIST_EMAIL", "admin@example.com")
    password = os.getenv("GRIST_PASSWORD", "admin")
    return email, password


@pytest.fixture
def logged_in_page(page: Page, grist_url: str, grist_credentials: tuple[str, str]) -> Page:
    """Navigate to Grist and login."""
    email, password = grist_credentials
    
    # Navigate to Grist
    page.goto(grist_url)
    
    # Check if login is required (first-run)
    if page.locator("text=Sign in").is_visible():
        # Handle initial setup or login
        page.fill("input[type='email']", email)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
    
    return page
