# Athena Testing Framework

## Quick Start

### 1. Install Testing Dependencies

```bash
chmod +x setup-tests.sh
./setup-tests.sh
```

This will:
- Install Playwright for E2E testing
- Install pytest and dependencies
- Create test result directories
- Run initial smoke tests

### 2. Run Tests

```bash
# Run all E2E tests
npx playwright test

# Run all API tests
pytest tests/api/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test file
npx playwright test tests/e2e/tests/auth/login.spec.ts
```

---

## Test Structure

```
tests/
├── e2e/                    # Playwright E2E tests
│   ├── pages/              # Page Object Models
│   │   ├── LoginPage.ts
│   │   ├── CharterListPage.ts
│   │   ├── CharterDetailPage.ts
│   │   └── DriverDashboardPage.ts
│   ├── tests/
│   │   ├── auth/           # Authentication tests
│   │   ├── charters/       # Charter management tests
│   │   ├── drivers/        # Driver dashboard tests
│   │   └── accounting/     # AR/AP tests
│   └── playwright.config.ts
├── api/                    # API integration tests
│   ├── test_smoke.py       # Health checks
│   ├── test_charter_api.py # Charter endpoints
│   └── test_auth_api.py    # Auth endpoints
├── integration/            # Cross-service tests
│   └── test_charter_workflow.py
├── performance/            # Load tests
│   └── locustfile.py
├── conftest.py            # Pytest configuration
└── requirements.txt       # Python dependencies
```

---

## Test Coverage

### E2E Tests (Playwright)
- ✅ Login/logout all roles
- ✅ Charter list display
- ✅ Charter filtering
- ✅ Role-based access control
- 🔄 Charter creation (coming)
- 🔄 Charter workflow (coming)
- 🔄 Document upload (coming)
- 🔄 Driver dashboard (coming)

### API Tests (pytest)
- ✅ Health checks (all services)
- ✅ Authentication
- ✅ Charter CRUD
- ✅ Pricing validation
- ✅ Driver endpoints
- 🔄 Document API (coming)
- 🔄 Payment API (coming)

### Integration Tests
- 🔄 Complete charter lifecycle
- 🔄 Payment flow
- 🔄 Email notifications

---

## Running Tests

### E2E Tests

```bash
# Run all tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run specific test file
npx playwright test tests/e2e/tests/auth/login.spec.ts

# Run specific test
npx playwright test -g "should login successfully as admin"

# Generate HTML report
npx playwright show-report

# Debug mode
npx playwright test --debug
```

### API Tests

```bash
# Run all API tests
pytest tests/api/ -v

# Run with coverage
pytest tests/api/ -v --cov --cov-report=html

# Run specific test file
pytest tests/api/test_charter_api.py -v

# Run specific test
pytest tests/api/test_charter_api.py::TestCharterAPI::test_list_charters -v

# Run only smoke tests
pytest tests/api/ -v -m smoke

# Run in parallel
pytest tests/api/ -v -n auto
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific workflow test
pytest tests/integration/test_charter_workflow.py -v
```

### Performance Tests

```bash
# Start Locust web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8080

# Access at http://localhost:8089
# Set number of users and spawn rate
```

---

## Test Reports

### Playwright Reports
- **Location**: `playwright-report/`
- **Open**: `npx playwright show-report`
- Includes screenshots and videos of failures

### Pytest Coverage
- **HTML Report**: `coverage/index.html`
- **XML Report**: `coverage/coverage.xml` (for CI/CD)

### Test Results
- **JUnit XML**: `test-results/junit.xml`
- Compatible with CI/CD systems

---

## CI/CD Integration

Tests are configured to run in GitHub Actions:

```yaml
# .github/workflows/tests.yml
- Run on push to main/develop
- Run on pull requests
- Parallel execution
- Coverage reporting
- Artifact uploads
```

---

## Troubleshooting

### Playwright Issues

```bash
# Reinstall browsers
npx playwright install --with-deps

# Check Playwright version
npx playwright --version

# Update Playwright
npm install --save-dev @playwright/test@latest
```

### Pytest Issues

```bash
# Reinstall dependencies
pip install -r tests/requirements.txt --force-reinstall

# Check pytest version
pytest --version

# Clear pytest cache
pytest --cache-clear
```

### Test Failures

1. **Check system is running**: `./start-all.sh`
2. **Check services are healthy**: `podman-compose ps`
3. **View logs**: `podman-compose logs [service-name]`
4. **Reset database**: Reseed with known test data

---

## Best Practices

### Writing Tests

1. **Use Page Object Models** for E2E tests
2. **Keep tests independent** - no interdependencies
3. **Use fixtures** for common setup
4. **Test one thing per test** - focused assertions
5. **Use descriptive test names** - what and why
6. **Clean up after tests** - database rollback, file cleanup

### Test Data

1. **Use seed data** for read-only tests
2. **Create fresh data** for write tests
3. **Use fixtures** for reusable test data
4. **Reset database** between test runs if needed

### Performance

1. **Run in parallel** when possible (`-n auto`)
2. **Use headless mode** for CI/CD
3. **Mock external services** when appropriate
4. **Use transactions** for database tests

---

## Next Steps

### Week 2-3: Expand E2E Coverage
- Charter creation and editing
- Document upload workflows
- Driver dashboard tests
- Accounting page tests

### Week 3-4: Complete API Tests
- All 6 microservices
- Error handling
- Edge cases
- Performance validation

### Week 4-5: Integration Tests
- Complete charter lifecycle
- Payment processing flow
- Email notification flow
- Airflow DAG testing

### Week 5-6: Performance & CI/CD
- Load testing with Locust
- Stress testing
- GitHub Actions integration
- Automated deployments

---

## Resources

- **Playwright Docs**: https://playwright.dev
- **Pytest Docs**: https://docs.pytest.org
- **Locust Docs**: https://docs.locust.io
- **Testing Plan**: See TESTING_PLAN.md for full implementation roadmap
