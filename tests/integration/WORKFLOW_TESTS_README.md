# Comprehensive Workflow Test Suite

This test suite validates all major workflows end-to-end across the CoachWay platform.

## Prerequisites

1. **System must be running:**
   ```bash
   ./start-all.sh
   ```

2. **Verify all services are healthy:**
   ```bash
   docker ps | grep athena
   ```

3. **Required tools:**
   - `curl`
   - `jq`
   - `bash` 4.0+

## Running All Workflows

Execute the comprehensive test suite:

```bash
bash tests/integration/run_all_workflows.sh
```

## Test Coverage

### 10 Complete Workflows Tested:

#### **Workflow 1: Lead to Charter Conversion**
- **Services:** Sales → Charter → Pricing
- **Tests:** Lead creation → qualification → activity logging → charter creation → quote calculation
- **Script:** `workflow_test_001.sh`

#### **Workflow 2: Charter Bidding Process**  
- **Services:** Charter → Vendor
- **Tests:** Charter creation → vendor bid requests → bid evaluation → bid acceptance/rejection
- **Script:** `workflow_test_002_charter_bidding.sh`

#### **Workflow 3: Vendor Selection & Compliance**
- **Services:** Vendor → Charter
- **Tests:** Vendor filtering → compliance checking → bid creation → vendor selection → charter assignment
- **Script:** `workflow_test_003_vendor_selection.sh`

#### **Workflow 4: Charter Share Links (Phase 8 Task 8.4)**
- **Services:** Charter → Kong Gateway
- **Tests:** Share link creation → viewing → verification → deletion
- **Routes:** `/api/v1/charters/{id}/share`, `/api/v1/charters/share/{token}`

#### **Workflow 5: Document E-Signature System (Phase 8 Task 8.5)**
- **Services:** Document → Kong Gateway
- **Tests:** Document upload → signature request → signature tracking → reminders
- **Routes:** `/api/v1/documents/{id}/request-signature`, `/api/v1/documents/signature-requests/{id}`

#### **Workflow 6: Change Management**
- **Services:** Change Management → Charter → Pricing
- **Tests:** Change case creation → review → approval → implementation
- **States:** New → In Review → Approved → Implemented

#### **Workflow 7: Payment Processing**
- **Services:** Charter → Payment
- **Tests:** Client payment creation → payment status updates → vendor payment scheduling

#### **Workflow 8: Portal Aggregation**
- **Services:** Portal → Charter → Client → Vendor (BFF pattern)
- **Tests:** Dashboard data aggregation → user preferences → activity logging

#### **Workflow 9: Pricing & Quote Generation**
- **Services:** Pricing → Charter
- **Tests:** Quote calculation → quote submission → pricing history

#### **Workflow 10: Kong API Gateway Routes**
- **Services:** Kong Gateway → All Backend Services
- **Tests:** Phase 8 routes accessibility → path routing → service connectivity

## Individual Workflow Tests

Run specific workflows:

```bash
# Lead to Charter
bash tests/integration/workflow_test_001.sh

# Charter Bidding
bash tests/integration/workflow_test_002_charter_bidding.sh

# Vendor Selection
bash tests/integration/workflow_test_003_vendor_selection.sh
```

## Test Output

### Console Output
- Real-time progress with color-coded results
- Step-by-step execution details
- Success/failure indicators

### Log File
Detailed logs saved to `/tmp/workflow_test_YYYYMMDD_HHMMSS.log`

### Test Summary Example:
```
================================================================
TEST SUMMARY
================================================================
Total Workflows: 10
Passed: 10
Failed: 0

✅ ALL WORKFLOWS PASSED!
```

## Understanding Test Results

### Success Indicators:
- ✅ **PASSED** - Workflow completed successfully
- ✓ **Step completed** - Individual step succeeded

### Failure Indicators:
- ❌ **FAILED** - Workflow failed
- ✗ **Step failed** - Individual step failed

### Warnings:
- ⚠ **Warning** - Non-critical issue (service unavailable, alternative path taken)
- ⊘ **SKIPPED** - Test skipped (service not available)

## Common Issues

### All Services Not Responding
```bash
# Start the system
./start-all.sh

# Wait for services to be healthy (30-60 seconds)
watch docker ps

# Retry tests
bash tests/integration/run_all_workflows.sh
```

### Authentication Failures
```bash
# Verify auth service is running
curl http://localhost:8080/api/v1/auth/health

# Check credentials in test script match your setup
```

### Kong Gateway Routes Failing
```bash
# Verify Kong is running
curl http://localhost:8081/services

# Check Phase 8 routes documentation
cat docs/PHASE8_KONG_ROUTES.md
```

## Test Data

### Default Test Users:
- **Admin:** `admin@athena.com` / `admin123`
- **Manager:** `manager@athena.com` / `admin123`
- **Agent:** `agent@athena.com` / `admin123`

### Test Entities Created:
- Leads (Sales service)
- Charters (Charter service)
- Bids (Vendor service)
- Payments (Charter service)
- Documents (Document service)
- Share links (Charter service)
- Change cases (Change Management service)

## Continuous Integration

This test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Workflow Tests
  run: |
    ./start-all.sh
    sleep 60  # Wait for services
    bash tests/integration/run_all_workflows.sh
```

## Performance Metrics

Expected execution times:
- Full suite: ~2-3 minutes
- Individual workflow: 10-30 seconds each
- Health checks: ~5 seconds

## Maintenance

### Adding New Workflows

1. Create new test function in `run_all_workflows.sh`:
   ```bash
   test_workflow_N_your_workflow() {
       print_header "WORKFLOW N: Your Workflow Name"
       # Test steps...
       workflow_passed "Your Workflow"
   }
   ```

2. Add to main execution:
   ```bash
   test_workflow_N_your_workflow
   ```

3. Document in this README

### Updating Existing Tests

- Individual workflow scripts: `workflow_test_00*.sh`
- Main test suite: `run_all_workflows.sh`
- Keep documentation in sync

## Related Documentation

- [Phase 8 Kong Routes](../docs/PHASE8_KONG_ROUTES.md)
- [Testing Plan](../docs/testing_plan.md)
- [Workflow Test Report](../docs/WORKFLOW_TEST_REPORT.md)
- [API Documentation](../docs/README.md)

## Support

For issues or questions:
1. Check logs in `/tmp/workflow_test_*.log`
2. Verify service health with `docker ps`
3. Review Kong configuration with `curl http://localhost:8081/services`
4. Check individual service logs: `docker logs athena-<service-name>`

---

**Last Updated:** February 4, 2026  
**Test Suite Version:** 1.0.0  
**Coverage:** 10 major workflows across 8 microservices
