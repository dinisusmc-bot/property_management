/**
 * Phase 2.2 Manual Payment Application Tests
 * Tests payment override form, validation, and backend integration
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, requestWithRetry } from '../../fixtures/api-helpers';
import { safeClick } from '../../fixtures/ui-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const goToManualPayment = async (page: any) => {
  // Navigate to a charter detail first to access manual payment
  await page.goto('/charters');
  await page.waitForLoadState('domcontentloaded');
};

const buildPaymentOverridePayload = (overrides: Record<string, any> = {}) => {
  const stamp = Date.now();
  return {
    charter_id: 1,
    payment_type: 'check',
    amount: 250.00,
    payment_date: new Date().toISOString().split('T')[0],
    reference_number: `PAY-${stamp}`,
    notes: 'Manual payment override test',
    ...overrides,
  };
};

const createPaymentOverride = async (request: any, overrides: Record<string, any> = {}) => {
  const payload = buildPaymentOverridePayload(overrides);
  const headers = await getAdminAuthHeaders(request);
  const response = await requestWithRetry(
    request,
    'post',
    `${KONG_BASE_URL}/api/v1/payments/override`,
    {
      headers,
      data: payload,
      timeout: 60000,
    },
  );
  expect(response.ok()).toBeTruthy();
  const payment = await response.json();
  return { payment, payload };
};

test.describe('Manual Payment Application - UI Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/charters');
    await page.waitForLoadState('domcontentloaded');
  });

  test('should display manual payment form when triggered', async ({ page }) => {
    // Click on a charter to open payment form
    const charterRow = page.getByRole('row').nth(1);
    await safeClick(page, charterRow);
    await page.waitForURL(/.*\/charters\/\d+/);

    // Look for manual payment button/link
    const paymentButton = page.getByRole('button', { name: /manual payment/i });
    await expect(paymentButton).toBeVisible();
  });

  test('should show payment override form fields', async ({ page }) => {
    const charterRow = page.getByRole('row').nth(1);
    await safeClick(page, charterRow);
    await page.waitForURL(/.*\/charters\/\d+/);

    await page.getByRole('button', { name: /manual payment/i }).click();

    await expect(page.getByLabel(/payment type/i)).toBeVisible();
    await expect(page.getByLabel(/amount/i)).toBeVisible();
    await expect(page.getByLabel(/payment date/i)).toBeVisible();
    await expect(page.getByLabel(/reference number/i)).toBeVisible();
    await expect(page.getByLabel(/notes/i)).toBeVisible();
  });
});

test.describe('Manual Payment Application - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should create payment override via API', async ({ request }) => {
    const { payment, payload } = await createPaymentOverride(request);

    expect(payment.id).toBeDefined();
    expect(payment.charter_id).toBe(payload.charter_id);
    expect(payment.amount).toBe(payload.amount);
    expect(payment.payment_type).toBe(payload.payment_type);
    expect(payment.reference_number).toBe(payload.reference_number);
  });

  test('should validate amount is positive', async ({ page, request }) => {
    const payload = buildPaymentOverridePayload({ amount: -50.00 });
    const headers = await getAdminAuthHeaders(request);
    
    const response = await request.post(
      `${KONG_BASE_URL}/api/v1/payments/override`,
      {
        headers,
        data: payload,
        timeout: 60000,
      }
    );

    expect(response.ok()).toBeFalsy();
    const error = await response.json();
    expect(error.detail).toContain('positive');
  });

  test('should persist payment override after page refresh', async ({ page, request }) => {
    const { payment, payload } = await createPaymentOverride(request);

    // Navigate to a charter detail page
    await page.goto('/charters');
    await page.waitForLoadState('domcontentloaded');

    // Refresh page
    await page.reload();
    
    // Look for the payment reference
    await expect(page.getByText(payload.reference_number).or(page.getByText(`${payload.amount.toFixed(2)}`))).toBeVisible({
      timeout: 10000
    });
  });

  test('should fetch payment history from backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/payments`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(Array.isArray(data)).toBeTruthy();
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('amount');
      expect(data[0]).toHaveProperty('payment_type');
      expect(data[0]).toHaveProperty('charter_id');
    }
  });

  test('should create manual payment with check type', async ({ request }) => {
    const payload = buildPaymentOverridePayload({
      payment_type: 'check',
      reference_number: 'CHECK-12345'
    });
    
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'post',
      `${KONG_BASE_URL}/api/v1/payments/manual`,
      {
        headers,
        data: payload,
        timeout: 60000,
      },
    );
    
    expect(response.ok()).toBeTruthy();
    const payment = await response.json();
    
    expect(payment.payment_type).toBe('check');
    expect(payment.reference_number).toBe('CHECK-12345');
  });

  test('should validate required fields', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    
    // Test missing amount
    const response1 = await request.post(
      `${KONG_BASE_URL}/api/v1/payments/override`,
      {
        headers,
        data: {
          charter_id: 1,
          payment_type: 'check',
          payment_date: new Date().toISOString().split('T')[0],
        },
        timeout: 60000,
      }
    );
    
    expect(response1.ok()).toBeFalsy();
    
    // Test missing payment date
    const response2 = await request.post(
      `${KONG_BASE_URL}/api/v1/payments/override`,
      {
        headers,
        data: {
          charter_id: 1,
          payment_type: 'check',
          amount: 100,
        },
        timeout: 60000,
      }
    );
    
    expect(response2.ok()).toBeFalsy();
  });
});

test.describe('Manual Payment Application - Complete Workflow', () => {
  test('should complete manual payment workflow end-to-end', async ({ page, request }) => {
    // Step 1: Navigate to charter
    await page.goto('/charters');
    await page.waitForLoadState('domcontentloaded');

    // Step 2: Open charter detail
    const charterRow = page.getByRole('row').nth(1);
    await safeClick(page, charterRow);
    await page.waitForURL(/.*\/charters\/\d+/);

    // Step 3: Open manual payment
    await page.getByRole('button', { name: /manual payment/i }).click();

    // Step 4: Fill form
    await page.getByLabel(/amount/i).fill('150.00');
    await page.getByLabel(/payment date/i).fill(new Date().toISOString().split('T')[0]);
    await page.getByLabel(/reference number/i).fill(`PAY-${Date.now()}`);

    // Step 5: Submit
    await page.getByRole('button', { name: /apply payment/i }).click();

    // Step 6: Verify success message
    await expect(page.getByText(/payment override applied/i).or(page.getByText(/success/i))).toBeVisible({
      timeout: 10000
    });

    // Step 7: Verify backend persistence
    const headers = await getAdminAuthHeaders(request);
    const paymentsResponse = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/payments`,
      { headers, timeout: 60000 },
    );
    
    const payments = await paymentsResponse.json();
    const newPayment = payments.find((p: any) => p.amount === 150);
    
    expect(newPayment).toBeDefined();
    expect(newPayment.amount).toBe(150);
  });
});
