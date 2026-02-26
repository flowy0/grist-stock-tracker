# UI Testing Strategies for Grist Stock Tracker

This document outlines automated UI testing approaches for the Grist Stock Tracker project.

## Overview

Grist Stock Tracker has two layers that can be tested:
1. **Backend/Data Layer** - Python scripts that interact with Grist API (already covered by unit tests)
2. **UI Layer** - Grist spreadsheet interface where users interact with data

## Testing Approaches

### 1. API-Based Testing (Recommended Primary Approach)

Since Grist provides a comprehensive REST API, most functionality can be tested via API calls without a browser.

**What to test via API:**
- Data import to bronze_transactions
- Data transformation to silver_transactions
- Formula calculations in gold_positions
- Record creation, updates, and deletion
- Table schema validation

**Benefits:**
- Fast execution
- Reliable (no flaky UI interactions)
- Easy to integrate with CI/CD
- Already implemented in `scripts/tests/`

**Tools:**
- Python `requests` library (already used in project)
- pytest for test framework

**Example:**
```python
# Already implemented in test_csv_import.py, test_bronze_to_silver.py
```

---

### 2. End-to-End Browser Testing (For Critical User Flows)

For testing actual user interactions with the Grist UI.

**When to use:**
- Testing formula editing in Grist UI
- Testing user permissions and access control
- Testing complex multi-step user workflows
- Visual regression testing

**Recommended Tool: Playwright**

Playwright is recommended over Cypress for this project because:
- **Multi-tab support** - Can test workflows that open new tabs
- **Cross-browser** - Supports Chrome, Firefox, Safari (WebKit)
- **API + UI testing** - Can mix API calls with UI interactions
- **Built-in parallelization** - Free, no paid service required
- **Trace viewer** - Excellent debugging capabilities
- **Python support** - Consistent with project tech stack

**Installation:**
```bash
cd scripts
uv add --dev playwright
uv run playwright install
```

**Example Test Structure:**
```python
# tests/test_grist_ui.py
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def grist_page(page: Page):
    """Login to Grist and return authenticated page."""
    page.goto("http://localhost:8484")
    # Login flow
    page.fill("[name=email]", "admin@localhost")
    page.click("button[type=submit]")
    return page

def test_bronze_table_visible(grist_page: Page):
    """Test that bronze_transactions table is accessible."""
    grist_page.goto("http://localhost:8484/o/docs/doc/{DOC_ID}/p/1")
    expect(grist_page.locator("text=bronze_transactions")).to_be_visible()

def test_import_data_flow(grist_page: Page):
    """Test data import workflow."""
    # Navigate to import page
    grist_page.click("text=Add New")
    grist_page.click("text=Import from file")
    
    # Upload file
    grist_page.set_input_files("input[type=file]", "samples/sample-minimal-test.csv")
    
    # Verify import success
    expect(grist_page.locator("text=Import successful")).to_be_visible()
```

---

### 3. Formula Testing Strategy

Grist formulas are Python-based and run in a sandboxed environment.

**Approach 1: Unit Tests (Preferred)**
Test formula logic in Python unit tests:

```python
# tests/test_formulas.py

def test_total_fees_calculation():
    """Test Total_Fees formula logic."""
    platform_fees = 0.99
    tax = 0.19
    settlement_fees = 0.0
    trading_fees = 0.0
    cat_fees = 0.0
    commission = 0.99
    clearing_fees = 0.09
    
    result = sum([platform_fees, tax, settlement_fees, 
                  trading_fees, cat_fees, commission, clearing_fees])
    
    assert result == 2.26

def test_net_amount_buy():
    """Test Net_Amount for Buy transaction."""
    fill_amount = 2910.00
    total_fees = 2.28
    side = "Buy"
    
    if side == "Buy":
        net_amount = fill_amount + total_fees
    else:
        net_amount = fill_amount - total_fees
    
    assert net_amount == 2912.28
```

**Approach 2: API Integration Tests**
Test formulas via Grist API by inserting data and reading results:

```python
# tests/test_grist_formulas.py

def test_gold_position_calculations():
    """Test that gold_positions formulas calculate correctly."""
    # Insert test transaction via API
    grist_api.add_records("silver_transactions", [{
        "Symbol": "TEST",
        "Side": "Buy",
        "Fill_Qty": 100,
        "Fill_Price": 10.0,
        "Net_Amount": 1000.0
    }])
    
    # Read calculated position
    positions = grist_api.get_records("gold_positions")
    test_position = [p for p in positions if p["fields"]["Symbol"] == "TEST"][0]
    
    assert test_position["fields"]["Total_Shares"] == 100
    assert test_position["fields"]["Avg_Cost_Basis"] == 10.0
```

---

### 4. Visual Regression Testing

For catching unintended UI changes.

**When to use:**
- After Grist version updates
- After formula changes that affect display
- After table configuration changes

**Tool: Playwright with screenshot comparison**

```python
# tests/test_visual_regression.py
from playwright.sync_api import Page

def test_bronze_table_snapshot(grist_page: Page):
    """Capture screenshot of bronze_transactions table."""
    grist_page.goto("http://localhost:8484/o/docs/doc/{DOC_ID}/p/1")
    
    # Wait for table to load
    grist_page.wait_for_selector(".grist-table")
    
    # Take screenshot
    expect(grist_page.locator(".grist-table")).to_have_screenshot(
        "bronze_table.png",
        threshold=0.2  # Allow 20% pixel difference
    )
```

---

## Test Pyramid for Grist Stock Tracker

```
        /\
       /  \
      / UI \          <- Browser tests (5-10% of tests)
     /________\         Critical user flows only
    /          \
   /   API      \     <- API integration tests (20-30%)
  /______________\       Formula validation, data flow
 /                \
/    Unit Tests    \   <- Unit tests (60-70%)
/____________________\   Business logic, calculations
```

**Recommended Distribution:**
- **Unit Tests:** 70% - Business logic, formula calculations, data transformations
- **API Tests:** 25% - Grist API integration, data pipeline validation
- **UI Tests:** 5% - Critical user flows, visual regression

---

## Implementation Roadmap

### Phase 1: API Testing (Current - Implemented) ✅
- Unit tests for Python scripts
- API client tests
- Data transformation tests

### Phase 2: Playwright Setup (Recommended Next)
```bash
# Install Playwright
cd scripts
uv add --dev playwright pytest-playwright
uv run playwright install

# Create UI test directory
mkdir tests/ui
```

### Phase 3: Critical Path UI Tests
Priority tests to implement:
1. **Login flow** - Verify authentication works
2. **Table navigation** - Verify all tables are accessible
3. **Data import** - Test CSV import through UI
4. **Formula verification** - Spot-check calculated values display correctly

### Phase 4: Visual Regression (Optional)
- Set up screenshot comparison
- Establish baseline images
- Run on every Grist version update

---

## Running Tests

### Unit + API Tests (Fast - Run on every commit)
```bash
cd scripts
uv run pytest tests/ -v
```

### UI Tests (Slower - Run before releases)
```bash
cd scripts
# Start Grist if not running
docker-compose up -d

# Run UI tests
uv run pytest tests/ui/ -v --headed  # Show browser
uv run pytest tests/ui/ -v           # Headless mode
```

### All Tests with Coverage
```bash
cd scripts
uv run pytest tests/ --cov=. --cov-report=html
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run tests
        run: |
          cd scripts
          uv run pytest tests/ -v

  ui-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - name: Start Grist
        run: docker-compose up -d
      - name: Run UI tests
        run: |
          cd scripts
          uv run pytest tests/ui/ -v
```

---

## Best Practices

### 1. Test Data Management
- Use separate test document in Grist for testing
- Clean up test data after each test
- Use fixtures for consistent test data

### 2. Selector Strategy
- Use data-testid attributes for stable selectors
- Avoid CSS/XPath selectors that change with styling

```python
# Good
page.click("[data-testid='import-button']")

# Bad - brittle
page.click(".btn-primary:nth-child(2)")
```

### 3. Flakiness Prevention
- Use explicit waits, not sleep
- Wait for API responses
- Retry failed assertions

```python
# Good
page.wait_for_selector(".table-loaded")
expect(page.locator(".row")).to_have_count(10)

# Bad
import time
time.sleep(5)  # Don't do this
```

### 4. Test Independence
- Each test should create its own data
- Don't rely on test execution order
- Clean up in teardown

---

## Tools Comparison

| Feature | Playwright (Recommended) | Cypress | Selenium |
|---------|--------------------------|---------|----------|
| **Browser Support** | Chrome, Firefox, Safari | Chrome, Firefox, Edge | All browsers |
| **Multi-tab** | ✅ Yes | ❌ No | ✅ Yes |
| **Python Support** | ✅ Yes | ❌ JS/TS only | ✅ Yes |
| **Parallel (Free)** | ✅ Yes | ❌ Paid only | ✅ Yes |
| **API Testing** | ✅ Built-in | ✅ Yes | ⚠️ Additional libs |
| **Speed** | Fast | Fast | Slower |
| **Learning Curve** | Medium | Low | High |
| **Community** | Growing | Large | Very large |
| **Mobile Testing** | ✅ Emulation | ❌ Limited | ✅ Via Appium |

**Recommendation:** Use **Playwright** for new UI tests in this project due to Python support, multi-tab capability, and free parallelization.

---

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Grist API Reference](https://support.getgrist.com/api/)
- [pytest Documentation](https://docs.pytest.org/)
- [Test Pyramid Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)

---

## Summary

For Grist Stock Tracker, the recommended testing strategy is:

1. **Primary:** Unit + API tests (already implemented)
2. **Secondary:** Playwright UI tests for critical flows (future enhancement)
3. **Optional:** Visual regression tests (if needed)

This approach balances reliability, speed, and coverage while maintaining alignment with the project's Python-based tech stack.
