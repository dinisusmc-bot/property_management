# Automated Testing Implementation Plan

## Overview
Comprehensive testing strategy for Athena Charter Management System using Playwright (E2E), pytest (API/Integration), and containerized test execution.

---

## Phase 1: Foundation Setup (Week 1)

### Goals
- Set up testing infrastructure
- Create base test framework
- Implement CI/CD pipeline basics

### Tasks

#### 1.1 Create Testing Directory Structure
```
tests/
├── e2e/                      # Playwright end-to-end tests
│   ├── fixtures/             # Test data and setup
│   ├── pages/                # Page Object Models
│   ├── tests/
│   │   ├── auth/             # Login, logout, permissions
│   │   ├── charters/         # Charter CRUD and workflow
│   │   ├── clients/          # Client management
│   │   ├── vendors/          # Vendor management
│   │   ├── drivers/          # Driver dashboard
│   │   ├── accounting/       # AR/AP pages
│   │   └── documents/        # Document uploads
│   └── playwright.config.ts  # Playwright configuration
├── api/                      # API integration tests
│   ├── test_auth_api.py
│   ├── test_charter_api.py
│   ├── test_client_api.py
│   ├── test_document_api.py
│   ├── test_payment_api.py
│   └── test_notification_api.py
├── integration/              # Service integration tests
│   ├── test_charter_workflow.py
│   ├── test_payment_flow.py
│   ├── test_document_flow.py
│   └── test_airflow_dags.py
├── unit/                     # Unit tests (per service)
│   ├── auth/
│   ├── charters/
│   ├── clients/
│   ├── documents/
│   ├── notifications/
│   └── payments/
├── performance/              # Load and stress tests
│   └── locustfile.py
├── visual/                   # Visual regression tests
│   └── screenshots/
├── conftest.py              # Pytest fixtures
├── requirements.txt         # Python test dependencies
└── docker-compose.test.yml  # Test environment
```

#### 1.2 Install Testing Tools
```bash
# Frontend E2E testing
npm install --save-dev @playwright/test
npx playwright install

# Backend API testing
pip install pytest pytest-asyncio requests pytest-cov

# Performance testing
pip install locust

# Visual regression
pip install pytest-playwright playwright-screenshot
```

#### 1.3 Create Test Database
- Separate PostgreSQL database for tests
- Automated seeding with known test data
- Transaction rollback after each test
- Parallel test execution support

#### 1.4 Create Test Docker Compose
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: athena_test
      POSTGRES_USER: athena_test
      POSTGRES_PASSWORD: test_password
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed
  
  test-runner:
    build: ./tests
    depends_on:
      - test-postgres
    environment:
      DATABASE_URL: postgresql://athena_test:test_password@test-postgres/athena_test
    volumes:
      - ./tests:/tests
      - ./test-results:/test-results
```

---

## Phase 2: Core E2E Tests (Week 2-3)

### Priority Test Suites

#### 2.1 Authentication Flow
**File:** `tests/e2e/tests/auth/test_login.spec.ts`

```typescript
// Test cases:
- Login with admin credentials ✓
- Login with manager credentials ✓
- Login with vendor credentials ✓
- Login with driver credentials ✓
- Login with invalid credentials ✗
- Logout functionality ✓
- Session persistence ✓
- Auto-redirect based on role ✓
- Token expiration handling ✓
```

#### 2.2 Charter Management
**File:** `tests/e2e/tests/charters/test_charter_crud.spec.ts`

```typescript
// Test cases:
- Create new charter with itinerary ✓
- Edit charter details ✓
- Delete charter (admin only) ✓
- View charter detail page ✓
- List all charters with filters ✓
- Search charters by client/date ✓
- Assign vendor to charter ✓
- Assign driver to charter ✓
```

**File:** `tests/e2e/tests/charters/test_charter_workflow.spec.ts`

```typescript
// Test cases:
- Quote → Send for Approval (email sent) ✓
- Approved → Vendor Booked (upload doc) ✓
- Booked → Send Confirmation (email sent) ✓
- Confirmed → In Progress ✓
- In Progress → Completed ✓
- Workflow reversal/cancellation ✓
- Status color coding ✓
- Workflow buttons visibility by status ✓
```

#### 2.3 Pricing & Calculations
**File:** `tests/e2e/tests/charters/test_pricing.spec.ts`

```typescript
// Test cases:
- Base cost calculation (hours × rate) ✓
- Mileage cost calculation (miles × $2.50) ✓
- Additional fees (tolls, parking) ✓
- Vendor pricing (75% of client charge) ✓
- Client pricing (100%) ✓
- Profit margin calculation (25%) ✓
- Tax calculation ✓
- Discount application ✓
- Total calculation accuracy ✓
```

#### 2.4 Document Management
**File:** `tests/e2e/tests/documents/test_document_upload.spec.ts`

```typescript
// Test cases:
- Upload approval document ✓
- Upload booking document ✓
- Upload confirmation document ✓
- Upload PDF file ✓
- Upload Word document ✓
- Upload Excel file ✓
- Reject file >10MB ✗
- Reject invalid file type ✗
- Download document ✓
- Delete document (admin only) ✓
- Document list display ✓
```

#### 2.5 Driver Dashboard
**File:** `tests/e2e/tests/drivers/test_driver_dashboard.spec.ts`

```typescript
// Test cases:
- Driver sees only assigned charter ✓
- Charter details display correctly ✓
- Itinerary stops shown ✓
- Location tracking start/stop ✓
- Location updates every 2 minutes ✓
- Driver notes save correctly ✓
- No sidebar navigation visible ✓
- Auto-redirect to /driver on login ✓
- Cannot access admin pages ✗
```

#### 2.6 Accounting Pages
**File:** `tests/e2e/tests/accounting/test_accounts_receivable.spec.ts`

```typescript
// Test cases:
- List all client payments ✓
- Filter by date range ✓
- Filter by client ✓
- Record new payment ✓
- Client total charge shown (100%) ✓
- Additional fees included ✓
- Payment status updates ✓
- Invoice balance calculation ✓
```

**File:** `tests/e2e/tests/accounting/test_accounts_payable.spec.ts`

```typescript
// Test cases:
- List all vendor payments ✓
- Filter by date range ✓
- Filter by vendor ✓
- Record vendor payment ✓
- Vendor cost shown (75%) ✓
- Additional fees included ✓
- Payment status updates ✓
```

---

## Phase 3: API Integration Tests (Week 3-4)

### API Test Examples

#### 3.1 Charter API Tests
**File:** `tests/api/test_charter_api.py`

```python
import pytest
import requests

BASE_URL = "http://localhost:8080/api/v1"

@pytest.fixture
def auth_headers():
    """Get JWT token for tests"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@athena.com", "password": "admin123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_charters(auth_headers):
    """Test GET /charters endpoint"""
    response = requests.get(f"{BASE_URL}/charters/charters", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Validate schema
    assert "id" in data[0]
    assert "trip_date" in data[0]
    assert "status" in data[0]

def test_create_charter(auth_headers):
    """Test POST /charters endpoint"""
    payload = {
        "client_id": 1,
        "vehicle_id": 1,
        "trip_date": "2025-12-15",
        "passengers": 25,
        "trip_hours": 5.0
    }
    response = requests.post(
        f"{BASE_URL}/charters/charters",
        headers=auth_headers,
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["passengers"] == 25
    assert data["status"] == "quote"

def test_charter_pricing_calculation(auth_headers):
    """Test pricing engine accuracy"""
    response = requests.get(f"{BASE_URL}/charters/charters/1", headers=auth_headers)
    charter = response.json()
    
    # Verify vendor pricing is 75% of client
    vendor_total = (
        charter["vendor_base_cost"] +
        charter["vendor_mileage_cost"] +
        charter["vendor_additional_fees"]
    )
    client_total = (
        charter["client_base_charge"] +
        charter["client_mileage_charge"] +
        charter["client_additional_fees"]
    )
    
    assert vendor_total == pytest.approx(client_total * 0.75, rel=0.01)

def test_driver_endpoints(auth_headers):
    """Test driver-specific endpoints"""
    # Login as driver
    driver_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "driver1@athena.com", "password": "admin123"}
    )
    driver_token = driver_response.json()["access_token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    
    # Get assigned charter
    response = requests.get(
        f"{BASE_URL}/charters/charters/driver/my-charter",
        headers=driver_headers
    )
    assert response.status_code == 200
    charter = response.json()
    assert charter is not None
    
    # Update driver notes
    notes_response = requests.patch(
        f"{BASE_URL}/charters/charters/{charter['id']}/driver-notes",
        headers=driver_headers,
        json={"vendor_notes": "Test note from automation"}
    )
    assert notes_response.status_code == 200
```

#### 3.2 Document API Tests
**File:** `tests/api/test_document_api.py`

```python
def test_document_upload(auth_headers):
    """Test document upload endpoint"""
    with open("tests/fixtures/test.pdf", "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        data = {
            "charter_id": 1,
            "document_type": "approval",
            "description": "Test upload"
        }
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=auth_headers,
            files=files,
            data=data
        )
    assert response.status_code == 201
    doc = response.json()
    assert doc["file_name"] == "test.pdf"
    assert doc["charter_id"] == 1

def test_document_download(auth_headers):
    """Test document download"""
    # Upload first
    # ... upload code ...
    
    # Download
    response = requests.get(
        f"{BASE_URL}/documents/{doc_id}/download",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
```

#### 3.3 Payment API Tests
**File:** `tests/api/test_payment_api.py`

```python
def test_create_invoice(auth_headers):
    """Test invoice generation"""
    payload = {
        "charter_id": 1,
        "due_date": "2025-12-31",
        "payment_terms": "Net 30"
    }
    response = requests.post(
        f"{BASE_URL}/payments/invoices",
        headers=auth_headers,
        json=payload
    )
    assert response.status_code == 201
    invoice = response.json()
    assert invoice["invoice_number"].startswith("INV-")
    assert invoice["status"] == "draft"

def test_record_payment(auth_headers):
    """Test payment recording"""
    payload = {
        "invoice_id": 1,
        "amount": 500.00,
        "payment_method": "card",
        "payment_type": "deposit"
    }
    response = requests.post(
        f"{BASE_URL}/payments/payments",
        headers=auth_headers,
        json=payload
    )
    assert response.status_code == 201
    
    # Verify invoice balance updated
    invoice_response = requests.get(
        f"{BASE_URL}/payments/invoices/1",
        headers=auth_headers
    )
    invoice = invoice_response.json()
    assert invoice["amount_paid"] == 500.00
    assert invoice["balance_due"] == invoice["total"] - 500.00
```

---

## Phase 4: Integration Tests (Week 4-5)

### Workflow Integration Tests

#### 4.1 End-to-End Charter Workflow
**File:** `tests/integration/test_charter_workflow.py`

```python
def test_complete_charter_lifecycle():
    """Test full charter workflow from quote to completion"""
    
    # 1. Create charter (Quote)
    charter = create_charter(...)
    assert charter["status"] == "quote"
    
    # 2. Send for approval (email sent)
    approval_response = send_for_approval(charter["id"])
    assert approval_response["email_sent"] == True
    
    # 3. Upload approval document
    doc = upload_document(charter["id"], "approval", "approval.pdf")
    assert doc["document_type"] == "approval"
    
    # 4. Update status to Approved
    charter = update_charter_status(charter["id"], "approved")
    assert charter["status"] == "approved"
    
    # 5. Book vendor (upload booking doc)
    booking_doc = upload_document(charter["id"], "booking", "booking.pdf")
    charter = update_charter_status(charter["id"], "booked")
    assert charter["status"] == "booked"
    
    # 6. Send confirmation email
    confirmation = send_confirmation(charter["id"])
    assert confirmation["email_sent"] == True
    
    # 7. Update to Confirmed
    charter = update_charter_status(charter["id"], "confirmed")
    assert charter["status"] == "confirmed"
    
    # 8. Assign driver
    charter = assign_driver(charter["id"], driver_id=9)
    assert charter["driver_id"] == 9
    
    # 9. Start charter (In Progress)
    charter = update_charter_status(charter["id"], "in_progress")
    
    # 10. Driver updates location
    location = update_driver_location(charter["id"], "40.232550,-74.301440")
    assert location["last_checkin_location"] == "40.232550,-74.301440"
    
    # 11. Complete charter
    charter = update_charter_status(charter["id"], "completed")
    assert charter["status"] == "completed"
    
    # 12. Generate invoice
    invoice = generate_invoice(charter["id"])
    assert invoice["charter_id"] == charter["id"]
    assert invoice["total"] > 0
```

#### 4.2 Payment Flow Integration
**File:** `tests/integration/test_payment_flow.py`

```python
def test_payment_reminder_flow():
    """Test automated payment reminder system"""
    
    # 1. Create invoice
    invoice = create_invoice_with_due_date(days_from_now=5)
    
    # 2. Create payment schedule
    schedule = create_payment_schedule(invoice["id"], due_date=5_days_from_now)
    
    # 3. Trigger Airflow DAG (mock or actual)
    trigger_payment_reminder_dag()
    
    # 4. Wait for processing
    time.sleep(10)
    
    # 5. Verify reminder email sent
    email_logs = get_email_logs(charter_id=invoice["charter_id"])
    assert any(log["email_type"] == "upcoming_payment_reminder" for log in email_logs)
    
    # 6. Verify schedule updated
    schedule = get_payment_schedule(schedule["id"])
    assert schedule["last_reminder_sent"] is not None
```

---

## Phase 5: Performance & Load Tests (Week 5-6)

### Load Testing with Locust

#### 5.1 API Load Test
**File:** `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class CharterSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@athena.com",
            "password": "admin123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_charters(self):
        """Most common operation"""
        self.client.get("/api/v1/charters/charters", headers=self.headers)
    
    @task(2)
    def view_charter_detail(self):
        """View charter detail"""
        self.client.get("/api/v1/charters/charters/1", headers=self.headers)
    
    @task(1)
    def create_charter(self):
        """Less frequent operation"""
        payload = {
            "client_id": 1,
            "vehicle_id": 1,
            "trip_date": "2025-12-20",
            "passengers": 30,
            "trip_hours": 6.0
        }
        self.client.post("/api/v1/charters/charters", 
                        json=payload, 
                        headers=self.headers)
    
    @task(1)
    def list_documents(self):
        """Document listing"""
        self.client.get("/api/v1/documents/charter/1", headers=self.headers)
```

**Run load test:**
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8080
# Access UI: http://localhost:8089
```

---

## Phase 6: CI/CD Integration (Week 6)

### GitHub Actions Workflow

**File:** `.github/workflows/tests.yml`

```yaml
name: Automated Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      
      - name: Start test services
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30  # Wait for services
      
      - name: Run API tests
        run: |
          pytest tests/api/ -v --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          npm install
          npx playwright install --with-deps
      
      - name: Start application
        run: |
          ./start-all.sh
          sleep 60  # Wait for full startup
      
      - name: Run Playwright tests
        run: |
          npx playwright test
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Start full system
        run: ./start-all.sh
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

---

## Test Execution Commands

### Run All Tests
```bash
# API tests
pytest tests/api/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
npx playwright test

# Specific test file
npx playwright test tests/e2e/tests/charters/test_charter_workflow.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium

# Generate test report
npx playwright show-report
```

### Run Tests in Docker
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests in container
docker-compose -f docker-compose.test.yml run test-runner pytest tests/api/

# Clean up
docker-compose -f docker-compose.test.yml down
```

---

## Coverage & Reporting

### Coverage Targets
- **API Tests**: 80% code coverage
- **E2E Tests**: 100% user-facing features
- **Integration Tests**: All critical workflows
- **Performance Tests**: Baseline metrics established

### Test Reports
- HTML test reports generated after each run
- Screenshots on failure (Playwright)
- Video recordings of failed tests
- Coverage reports in XML/HTML formats
- Load test metrics exported to Grafana

---

## Maintenance & Best Practices

### Test Data Management
1. **Use fixtures** - Consistent test data across tests
2. **Database seeding** - Fresh data for each test run
3. **Transaction rollback** - Clean state after each test
4. **Test isolation** - No interdependencies

### Page Object Model
```typescript
// tests/e2e/pages/CharterDetailPage.ts
export class CharterDetailPage {
  constructor(private page: Page) {}
  
  async goto(charterId: number) {
    await this.page.goto(`/charters/${charterId}`);
  }
  
  async sendForApproval() {
    await this.page.click('button:has-text("Send for Approval")');
  }
  
  async uploadDocument(filePath: string, docType: string) {
    await this.page.setInputFiles('input[type="file"]', filePath);
    await this.page.selectOption('select[name="document_type"]', docType);
    await this.page.click('button:has-text("Upload")');
  }
  
  async getStatus() {
    return await this.page.textContent('.status-chip');
  }
}
```

### Continuous Monitoring
- Run critical tests every hour (smoke tests)
- Run full suite nightly
- Run on every PR
- Monitor test execution time trends
- Alert on test failures

---

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | Week 1 | Test infrastructure, directory structure, Docker setup |
| Phase 2 | Week 2-3 | Core E2E tests (auth, charters, documents, driver) |
| Phase 3 | Week 3-4 | API integration tests (all 6 services) |
| Phase 4 | Week 4-5 | Workflow integration tests |
| Phase 5 | Week 5-6 | Performance and load tests |
| Phase 6 | Week 6 | CI/CD pipeline integration |

**Total: 6 weeks to full test automation**

---

## ROI & Benefits

### Time Savings
- **Manual test cycle**: ~4 hours
- **Automated test cycle**: ~15 minutes
- **Savings per deployment**: 3.75 hours
- **Monthly deployments**: ~20
- **Monthly time saved**: ~75 hours

### Quality Improvements
- Catch regressions immediately
- Test all user roles consistently
- Validate complex calculations automatically
- Ensure cross-browser compatibility
- Monitor performance trends

### Confidence
- Deploy with confidence
- Faster feature iteration
- Reduced production bugs
- Better documentation (tests as specs)

---

## Next Steps

1. **Approve this plan**
2. **Create `tests/` directory structure**
3. **Set up Playwright and pytest**
4. **Write first smoke tests** (login, create charter, list charters)
5. **Expand coverage incrementally**
6. **Integrate into CI/CD**

Would you like me to start implementing Phase 1 now?
