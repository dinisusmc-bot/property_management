# Comprehensive End-to-End Workflow Tests

## Overview

This comprehensive E2E test suite validates all major workflows across the CoachWay platform's 13 microservices. Each workflow includes thorough data validation, cross-service integration testing, and state verification.

## Test Coverage

### Services Tested
- ✅ Auth Service (8080) - Authentication & Authorization
- ✅ Charter Service (8001) - Charter management
- ✅ Client Service (8002) - Client management
- ✅ Document Service (8003) - Document & E-signature
- ✅ Payment Service (8004) - Invoicing & payments
- ✅ Notification Service (8005) - Email/SMS notifications
- ✅ Sales Service (8006) - Lead & quote management
- ✅ Pricing Service (8007) - Dynamic pricing
- ✅ Vendor Service (8008) - Vendor management
- ✅ Dispatch Service (8009) - Driver & trip management
- ✅ Analytics Service (8010) - Reporting & metrics
- ✅ Portal Service (8011) - BFF & aggregation
- ✅ Change Management Service (8012) - Approval workflows

## Workflow Tests

### Workflow 1: Complete Client Onboarding & First Charter
**Purpose**: Test the full client lifecycle from creation to first charter booking

**Steps**:
1. Create new client with full profile data
2. Verify client retrieval and data integrity
3. Create first charter for the client
4. Update charter status to confirmed
5. Verify charter appears in client's charter list

**Validations**:
- Client ID, name, email, type, payment terms
- Charter ID, client association, status, passenger count, pricing
- Array length validation for client charters

**Data Created**: Client record, Charter record

---

### Workflow 2: Vendor Bidding & Selection Process
**Purpose**: Test the complete vendor bidding workflow

**Steps**:
1. Create vendor with compliance data
2. Submit bid for charter
3. List all bids for charter
4. Accept bid
5. Verify vendor assignment in charter
6. Check bid status updates

**Validations**:
- Vendor ID, name, type, active status
- Bid ID, amount, vehicle details
- Bid acceptance and status changes
- Vendor-charter assignment

**Data Created**: Vendor record, Bid record

---

### Workflow 3: Document Management & E-Signature Complete Flow
**Purpose**: Test document upload, e-signature requests, and completion

**Steps**:
1. Upload charter agreement document
2. Request e-signature via Kong API Gateway
3. List pending signatures
4. Simulate signature completion
5. Send signature reminder
6. Retrieve document with signature status

**Validations**:
- Document ID, type, charter association
- Signature request ID, signer details, document type
- Signature completion status
- Kong routing for document endpoints

**Data Created**: Document record, Signature request

---

### Workflow 4: Payment Processing End-to-End
**Purpose**: Test complete payment lifecycle from invoice to vendor payout

**Steps**:
1. Create client invoice with line items
2. Process client payment (credit card)
3. Simulate payment gateway response
4. Create vendor payout (ACH)
5. Verify payment summary for charter

**Validations**:
- Invoice ID, amounts (base, tax, total), status
- Payment ID, method, transaction details
- Payment processing and status updates
- Payout scheduling and amount verification
- Payment summary aggregation

**Data Created**: Invoice, Client Payment, Vendor Payout

---

### Workflow 5: Sales Pipeline & Quote to Charter Conversion
**Purpose**: Test lead management through conversion to booking

**Steps**:
1. Create sales lead with prospect data
2. Qualify lead and assign to sales rep
3. Generate quote via pricing service
4. Create quote record in sales system
5. Accept quote and convert to charter
6. Verify lead status changed to converted

**Validations**:
- Lead ID, contact details, status, passenger estimate
- Quote calculation and pricing
- Quote record creation and status
- Charter creation from conversion
- Lead status progression

**Data Created**: Lead, Quote, Converted Charter

---

### Workflow 6: Dispatch & Driver Assignment Complete Flow
**Purpose**: Test driver management and trip execution

**Steps**:
1. Create driver profile with credentials
2. Assign driver to charter
3. Send dispatch notification
4. Update trip status to in-progress
5. Complete trip with actuals
6. Get driver performance metrics

**Validations**:
- Driver ID, credentials, experience, status
- Dispatch assignment and associations
- Status transitions (assigned → in-progress → completed)
- Actual vs estimated data (duration, miles)
- Driver metrics aggregation

**Data Created**: Driver record, Dispatch assignment

---

### Workflow 7: Change Management & Approval Workflow
**Purpose**: Test change request lifecycle and approval process

**Steps**:
1. Create change request (passenger count increase)
2. Add impact assessment
3. Move to review status
4. Approve change
5. Implement change
6. Get change history for charter

**Validations**:
- Change request ID, type, priority, impact level
- Assessment data (cost, time, risk)
- Status progression (new → under_review → approved → implemented)
- Change history tracking

**Data Created**: Change case, Impact assessment

---

### Workflow 8: Multi-Channel Notification System
**Purpose**: Test notification delivery across channels

**Steps**:
1. Send charter confirmation email
2. Send SMS notification
3. Create notification template
4. Schedule future notification
5. Get notification history
6. Check delivery status

**Validations**:
- Email notification ID and status
- SMS notification creation
- Template ID, name, variables
- Scheduled notification timing
- Notification history aggregation
- Delivery status tracking

**Data Created**: Email notification, SMS notification, Template, Scheduled notification

---

### Workflow 9: Analytics & Reporting
**Purpose**: Test reporting capabilities and data aggregation

**Steps**:
1. Generate revenue report with projections
2. Get charter metrics for period
3. Get customer retention metrics
4. Generate vendor performance report
5. Get real-time dashboard data
6. Export report to CSV

**Validations**:
- Revenue totals and calculations
- Charter counts and metrics
- Retention rate percentage
- Vendor performance data
- Dashboard aggregated metrics
- Export file generation

**Data Created**: Reports, Exports

---

### Workflow 10: Portal BFF & Cross-Service Integration
**Purpose**: Test portal aggregation and multi-service data integration

**Steps**:
1. Get client portal dashboard (aggregates data from multiple services)
2. Get vendor portal dashboard
3. Get charter timeline (cross-service events)
4. Set user preferences
5. Log user activity
6. Get user activity history
7. Get system notifications

**Validations**:
- Client dashboard aggregation (charters, payments, documents)
- Vendor dashboard aggregation (trips, bids)
- Timeline event aggregation from multiple services
- Preference storage and retrieval
- Activity logging with entity tracking
- Activity history pagination
- Notification filtering

**Data Created**: User preferences, Activity logs

---

## Validation Framework

### Validation Types

1. **Field Existence Validation**: Ensures required fields are present in responses
2. **Field Value Validation**: Verifies field values match expected data
3. **Field Type Validation**: Checks data types (string, number, array, object)
4. **HTTP Code Validation**: Verifies API responses return expected status codes
5. **Array Length Validation**: Ensures collections have minimum expected items

### Validation Helpers

```bash
validate_field(response, field, expected, description)
validate_field_exists(response, field, description)
validate_field_type(response, field, type, description)
validate_http_code(code, expected, description)
validate_array_length(response, field, min_length, description)
```

## Test Execution

### Running All Tests
```bash
bash /home/nick/work_area/coachway_demo/tests/integration/run_all_workflows.sh
```

### Output

The test suite provides:
- **Color-coded console output**: Green for pass, red for fail, yellow for warnings
- **Main log file**: `/tmp/workflow_test_YYYYMMDD_HHMMSS.log`
- **Detailed log file**: `/tmp/workflow_test_detailed_YYYYMMDD_HHMMSS.log`

### Success Metrics

- **Workflow Success Rate**: Percentage of workflows that pass completely
- **Data Validation Success Rate**: Percentage of individual validations that pass
- **Total Validations**: Number of data checks performed across all workflows

## Prerequisites

1. All services must be running (use `./start-all.sh`)
2. Database must be seeded with test users:
   - admin@athena.com / admin123
   - manager@athena.com / admin123
   - agent@athena.com / admin123
3. Kong API Gateway configured and running
4. Network connectivity between services

## Test Data Management

- Tests create their own data rather than relying on fixtures
- IDs are captured and reused across workflows
- Global variables track created entities:
  - `CREATED_CLIENT_ID`
  - `CREATED_CHARTER_ID`
  - `CREATED_VENDOR_ID`
  - `CREATED_DOCUMENT_ID`
  - `CREATED_BID_ID`

## Integration Points Tested

### Service-to-Service
- Charter ↔ Client
- Charter ↔ Vendor
- Charter ↔ Document
- Charter ↔ Payment
- Charter ↔ Dispatch
- Lead ↔ Charter (conversion)
- Change Management ↔ Charter

### Via Kong Gateway
- `/api/v1/documents/{id}/request-signature`
- `/api/v1/documents/{id}/signatures`
- `/api/v1/charters/{id}/share`
- All service routes through gateway

### Portal Aggregation
- Client dashboard (charters + payments + documents)
- Vendor dashboard (trips + bids)
- Charter timeline (events from multiple services)

## Error Handling

- Graceful degradation for missing services
- Detailed error logging to detailed log file
- HTTP status code validation (200, 201, 404, 422)
- JSON parsing error handling
- Timeout handling for slow services

## Future Enhancements

1. **Performance Testing**: Add response time assertions
2. **Load Testing**: Concurrent workflow execution
3. **Negative Testing**: Invalid data scenarios
4. **Rollback Testing**: Transaction rollback verification
5. **Security Testing**: Authorization boundary tests
6. **Idempotency Testing**: Duplicate request handling

## Maintenance

### Adding New Workflows

1. Create workflow function: `test_workflow_N_description()`
2. Follow structure:
   - Print header with workflow name
   - Initialize start time and workflow_failed flag
   - Execute steps with print_subheader
   - Validate responses with validation helpers
   - Log detailed responses
   - Calculate duration
   - Call workflow_passed/workflow_failed
3. Add to main() execution list

### Updating Existing Workflows

- Maintain backward compatibility
- Add new validations without removing old ones
- Update expected values if service contracts change
- Document breaking changes

## Troubleshooting

### All Tests Failing
- Check if services are running: `docker ps | grep athena`
- Verify Kong is configured: `curl http://localhost:8081/services`
- Check authentication: Test token endpoint directly

### Specific Workflow Failing
- Review detailed log file for full responses
- Test service directly: `curl http://localhost:PORT/health`
- Check service logs: `docker logs athena-SERVICE-1`

### Validation Failures
- Compare expected vs actual in detailed log
- Verify service contract hasn't changed
- Check for data type mismatches (string vs number)

## Test Metrics

Expected results with all services healthy:
- **10 workflows** executed
- **80+ validations** performed
- **100% workflow success rate**
- **95%+ validation success rate**
- **Execution time**: 60-120 seconds

## Continuous Integration

### CI/CD Integration

```yaml
test:
  stage: test
  script:
    - ./start-all.sh
    - sleep 60  # Wait for services
    - bash tests/integration/run_all_workflows.sh
  artifacts:
    when: always
    paths:
      - /tmp/workflow_test_*.log
```

### GitHub Actions

```yaml
- name: Run E2E Tests
  run: |
    bash ./start-all.sh &
    sleep 60
    bash tests/integration/run_all_workflows.sh
```

## Documentation

- **Main README**: `tests/integration/WORKFLOW_TESTS_README.md`
- **Phase 8 Routes**: `docs/PHASE8_KONG_ROUTES.md`
- **Individual Workflows**: `tests/integration/workflow_test_*.sh`

## Contact

For questions or issues with the test suite, refer to:
- Test logs in `/tmp/workflow_test_*.log`
- Service documentation in `/docs`
- API documentation at `http://localhost:8080/docs` (Kong)
