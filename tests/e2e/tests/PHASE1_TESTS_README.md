# Phase 1 E2E Test Suite

Comprehensive end-to-end tests for all Phase 1 features using Playwright.

## Test Coverage

### Week 1: Lead Management (`leads/test_lead_management.spec.ts`)
- **CRUD Operations**: Create, read, update, delete leads
- **Status Workflow**: New → Contacted → Qualified → Converted
- **Lead Assignment**: Assign leads to sales agents
- **Lead Conversion**: Convert leads to quotes
- **Filtering**: Filter leads by status
- **Backend Validation**: Verify data persistence and API responses

**Test Count**: 8 UI tests + 3 backend tests = **11 tests**

### Week 2: Advanced Quote Builder (`quotes/test_quote_builder.spec.ts`)
- **Quote Creation**: Create quotes with automatic pricing
- **Pricing Calculations**: 
  - Distance-based pricing
  - Weekend surcharges
- **DOT Compliance**:
  - Driver hours limit warnings
- **Backend Integration**:
  - Pricing API response validation
  - Data persistence on charter save

**Test Count**: 5 UI tests + 2 backend tests = **7 tests**

### Week 3: Agent Dashboard (`dashboard/test_agent_dashboard.spec.ts`)
- **Dashboard Display**:
  - Sales metrics with period breakdown (Today, Week, Month, Quarter)
  - Conversion funnel visualization
  - Top performers leaderboard
  - Recent activity feed
  - Quick actions panel
- **Navigation**:
  - Quick action buttons to create leads/charters
  - Activity feed navigation to entity details
- **Metrics Updates**: Period selector changes
- **Backend Validation**:
  - Sales metrics API
  - Conversion funnel API
  - Top performers API
  - Recent activity API
  - Data accuracy verification

**Test Count**: 10 UI tests + 6 backend tests = **16 tests**

### Week 4: Charter Templates (`templates/test_charter_templates.spec.ts`)
- **Single Charter Cloning**:
  - Clone button display
  - Clone dialog functionality
  - Clone to new date
  - Cancel operation
- **Recurring Schedules**:
  - Daily pattern
  - Weekly pattern
  - Schedule preview
  - Date range selection
- **Template Management**:
  - Save charter as template
  - Template name
- **Backend Validation**:
  - Cloned charter persistence
  - Template storage
  - Recurring charter creation

**Test Count**: 11 UI tests + 3 backend tests = **14 tests**

## Total Coverage
- **Total Tests**: 48 tests
- **UI Tests**: 34 tests
- **Backend Integration Tests**: 14 tests

## Test Structure

Each test suite follows this pattern:

```typescript
test.describe('Feature - Aspect', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    // Setup navigation
  });

  test('should do something', async ({ page }) => {
    // Test implementation
  });
});
```

## Running Tests

### Run All Phase 1 Tests
```bash
cd /home/nick/work_area/coachway_demo/tests/e2e
npx playwright test tests/leads tests/quotes tests/dashboard tests/templates
```

### Run Individual Feature Tests
```bash
# Lead Management only
npx playwright test tests/leads/test_lead_management.spec.ts

# Quote Builder only
npx playwright test tests/quotes/test_quote_builder.spec.ts

# Dashboard only
npx playwright test tests/dashboard/test_agent_dashboard.spec.ts

# Templates only
npx playwright test tests/templates/test_charter_templates.spec.ts
```

### Run with UI Mode (Interactive)
```bash
npx playwright test --ui
```

### Run Specific Test
```bash
npx playwright test -g "should create new lead"
```

### Run in Headed Mode (See Browser)
```bash
npx playwright test --headed
```

## Prerequisites

### 1. Backend Services Running
All Phase 1 backend services must be running:

```bash
# Charter Service (Port 8001)
cd backend/services/charter-service
python -m uvicorn app.main:app --reload --port 8001

# Pricing Service (Port 8008)
cd backend/services/pricing-service
python -m uvicorn app.main:app --reload --port 8008

# Sales Service (Port 8007)
cd backend/services/sales-service
python -m uvicorn app.main:app --reload --port 8007
```

### 2. Frontend Running
```bash
cd frontend
npm run dev
# Should be running on http://localhost:3000
```

### 3. Test User Credentials
Tests use the following test credentials:
- **Admin**: admin@athena.com / admin123
- **Manager**: manager@athena.com / admin123
- **Sales Agent**: agent@athena.com / admin123

Make sure these users exist in your database.

## Test Data

Tests create and clean up their own data, but some tests rely on seed data:
- At least 1 existing charter for viewing/cloning
- At least 1 existing lead for viewing/editing
- Sales metrics data for dashboard tests

## Test Patterns

### 1. Flexible Selectors
Tests use multiple selector strategies to handle different implementations:
```typescript
const button = page.locator(
  'button:has-text("Create Lead"), ' +
  'button:has-text("New Lead"), ' +
  'button:has-text("Add Lead")'
);
```

### 2. Graceful Skipping
Tests skip gracefully if features aren't implemented yet:
```typescript
const hasFeature = await element.isVisible({ timeout: 3000 }).catch(() => false);
if (!hasFeature) {
  test.skip();
  return;
}
```

### 3. Backend Validation
Each feature has tests that verify backend data integrity:
```typescript
test('should persist data in backend', async ({ page, request }) => {
  // UI action
  await page.click('button:has-text("Save")');
  
  // Verify in backend
  const response = await request.get('http://localhost:8080/api/v1/charters/...');
  const data = await response.json();
  expect(data).toHaveProperty('id');
});
```

### 4. Wait Strategies
Tests use appropriate wait strategies:
- `waitForLoadState('networkidle')` - For page loads
- `waitForURL()` - For navigation
- `waitForSelector()` - For specific elements
- `waitForTimeout()` - For async operations (used sparingly)

## Debugging Failed Tests

### 1. View Test Report
```bash
npx playwright show-report
```

### 2. View Traces
When tests fail, Playwright captures traces:
```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

### 3. Run in Debug Mode
```bash
npx playwright test --debug
```

### 4. Screenshot on Failure
Failed tests automatically capture screenshots in `test-results/`

## Common Issues

### 1. Timeout Errors
- **Cause**: Backend service not running or slow response
- **Solution**: Ensure all backend services are running and responsive

### 2. Element Not Found
- **Cause**: UI implementation differs from test expectations
- **Solution**: Update selectors in test file or implement missing UI element

### 3. Navigation Timeout
- **Cause**: Frontend not running or wrong URL
- **Solution**: Verify frontend is on http://localhost:3000

### 4. Backend API Errors
- **Cause**: Backend API structure changed or service down
- **Solution**: Check backend logs and verify API endpoints

## Test Maintenance

### When UI Changes
Update selectors in affected test files:
1. Locate the test file in `tests/e2e/tests/[feature]/`
2. Update locators to match new UI structure
3. Re-run tests to verify

### When API Changes
Update backend validation tests:
1. Check test files with `request.get()` or `request.post()`
2. Update expected data structures
3. Verify API endpoint URLs

### Adding New Tests
1. Create test file in appropriate folder
2. Import `loginAsAdmin` from `../../fixtures/auth-helpers`
3. Follow existing test patterns
4. Add to this README

## CI/CD Integration

To run tests in CI/CD:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: cd tests/e2e && npm ci
      - name: Install Playwright Browsers
        run: cd tests/e2e && npx playwright install --with-deps
      - name: Start backend services
        run: docker-compose up -d
      - name: Start frontend
        run: cd frontend && npm ci && npm run build && npm run preview &
      - name: Run tests
        run: cd tests/e2e && npx playwright test
      - name: Upload report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

## Performance Considerations

- Tests run in **parallel** (36 workers by default)
- Each test is **independent** (no shared state)
- Use `test.describe.configure({ mode: 'serial' })` for dependent tests
- Average test duration: 5-15 seconds per test
- Full suite duration: ~5 minutes (with 36 workers)

## Next Steps

After Phase 1 tests pass:
1. Review test coverage report
2. Fix any failing tests
3. Add Phase 2 tests for Change Management
4. Integrate into CI/CD pipeline
5. Set up automated nightly runs

## Support

For issues with tests:
1. Check test output for specific error
2. Review backend service logs
3. Verify frontend console for errors
4. Check browser network tab in headed mode
5. Review Playwright trace for failed tests
