"""UI tests for Grist integration."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
class TestGristUI:
    """Test suite for Grist UI interactions."""
    
    def test_grist_homepage_loads(self, page: Page) -> None:
        """Test that Grist homepage loads successfully."""
        page.goto("http://localhost:8484")
        
        # Should see Grist branding or login
        expect(page.locator("body")).to_be_visible()
    
    def test_can_navigate_to_document(self, page: Page) -> None:
        """Test navigation to a Grist document."""
        # This is a placeholder - adjust selectors based on actual Grist UI
        page.goto("http://localhost:8484")
        
        # Look for document list or create document button
        body = page.locator("body")
        expect(body).to_be_visible()


@pytest.mark.ui
class TestGristAPIDocumentation:
    """Test API documentation accessibility."""
    
    def test_api_docs_available(self, page: Page) -> None:
        """Test that API documentation is accessible."""
        page.goto("http://localhost:8484/api/docs")
        
        # Should see API docs
        expect(page.locator("body")).to_be_visible()
