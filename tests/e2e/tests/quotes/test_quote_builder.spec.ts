/**
 * Advanced Quote Builder & Pricing Engine Tests - Phase 1 Week 2
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';


import { getKongBaseUrl, getAdminAuthHeaders, ensureClient, ensureVehicle } from '../../fixtures/api-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const selectFirstOption = async (page: any, label: string) => {
  const byRole = page.getByRole('combobox', { name: new RegExp(label, 'i') })
  const byIndex = page.getByRole('combobox').nth(label === 'Client' ? 0 : 1)
  const input = (await byRole.count()) > 0 ? byRole : byIndex

  await input.waitFor({ state: 'visible', timeout: 10000 })
  await expect(input).toBeEnabled({ timeout: 10000 })

  await input.click()

  const options = page.getByRole('option');
  await expect(options.first()).toBeVisible({ timeout: 10000 });
  await options.first().click();
};

const getTotalAmount = (page: any) => {
  const totalRow = page.getByRole('row', { name: /total/i });
  return totalRow.locator('h6').filter({ hasText: /\$[\d,.]+/ }).last();
};

test.describe('Advanced Quote Builder - Quote Creation', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page);
    await ensureClient(request);
    await ensureVehicle(request);
  });

  test('should display quote builder form', async ({ page }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /create charter/i })).toBeVisible();
    await expect(page.getByLabel('Trip Date')).toBeVisible();
    await expect(page.getByLabel('Number of Passengers')).toBeVisible();
  });

  test('should create quote with automatic pricing', async ({ page }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/failed to load clients and vehicles/i)).toBeHidden();

    await selectFirstOption(page, 'Client');
    await selectFirstOption(page, 'Vehicle');

    const tripDate = new Date();
    tripDate.setDate(tripDate.getDate() + 5);
    await page.getByLabel('Trip Date').fill(tripDate.toISOString().split('T')[0]);
    await page.getByLabel('Number of Passengers').fill('35');
    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('Napa Valley, CA');
    await page.getByLabel('Estimated Miles').fill('60');

    const totalAmount = getTotalAmount(page);
    await expect(totalAmount).toBeVisible({ timeout: 20000 });
  });

  test('should calculate price based on distance', async ({ page }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/failed to load clients and vehicles/i)).toBeHidden();

    await selectFirstOption(page, 'Client');
    await selectFirstOption(page, 'Vehicle');

    const tripDate = new Date();
    tripDate.setDate(tripDate.getDate() + 5);
    await page.getByLabel('Trip Date').fill(tripDate.toISOString().split('T')[0]);
    await page.getByLabel('Number of Passengers').fill('30');
    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('Oakland, CA');
    await page.getByLabel('Estimated Miles').fill('30');

    const totalAmount = getTotalAmount(page);
    await expect(totalAmount).toBeVisible({ timeout: 20000 });
    const shortDistancePrice = await totalAmount.textContent();

    await page.getByLabel('Estimated Miles').fill('200');
    await expect(totalAmount).toBeVisible({ timeout: 20000 });
    const longDistancePrice = await totalAmount.textContent();

    expect(longDistancePrice).not.toBe(shortDistancePrice);
  });
});

test.describe('Advanced Quote Builder - DOT Compliance', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page);
    await ensureClient(request);
    await ensureVehicle(request);
  });

  test('should warn about DOT hours limit', async ({ page }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/failed to load clients and vehicles/i)).toBeHidden();

    await selectFirstOption(page, 'Client');
    await selectFirstOption(page, 'Vehicle');

    const tripDate = new Date();
    tripDate.setDate(tripDate.getDate() + 5);
    await page.getByLabel('Trip Date').fill(tripDate.toISOString().split('T')[0]);
    await page.getByLabel('Number of Passengers').fill('40');
    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('Sacramento, CA');
    await page.getByLabel('Estimated Miles').fill('400');

    await page.getByRole('radio', { name: /hourly/i }).click();
    await page.getByLabel('Trip Duration (hours)').fill('12');

    await expect(page.getByText(/dot compliance warning/i)).toBeVisible({ timeout: 10000 });
  });

  test('should mark weekend trips in pricing summary', async ({ page }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/failed to load clients and vehicles/i)).toBeHidden();

    await selectFirstOption(page, 'Client');
    await selectFirstOption(page, 'Vehicle');

    const tripDate = new Date();
    tripDate.setDate(tripDate.getDate() + 5);
    await page.getByLabel('Trip Date').fill(tripDate.toISOString().split('T')[0]);
    await page.getByLabel('Number of Passengers').fill('30');
    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('San Jose, CA');
    await page.getByLabel('Estimated Miles').fill('50');

    await page.getByLabel('Weekend Service').check();

    await expect(page.getByText('Weekend', { exact: true })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Advanced Quote Builder - Backend Integration', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page);
    await ensureClient(request);
    await ensureVehicle(request);
  });

  test('should validate pricing API response structure', async ({ request }) => {
    const client = await ensureClient(request);
    const vehicle = await ensureVehicle(request);
    const headers = await getAdminAuthHeaders(request);
    const response = await request.post(`${KONG_BASE_URL}/api/v1/pricing/calculate-quote`, {
      headers,
      data: {
        client_id: client.id,
        vehicle_id: vehicle.id,
        trip_date: '2026-02-10',
        passengers: 30,
        total_miles: 50,
        trip_hours: 6,
        is_overnight: false,
        is_weekend: false,
        is_holiday: false,
        additional_fees: 0,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('breakdown');
    expect(data.breakdown.total_cost).toBeGreaterThan(0);
  });

  test('should save charter with calculated price to backend', async ({ page, request }) => {
    await page.goto('/charters/new');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/failed to load clients and vehicles/i)).toBeHidden();

    await selectFirstOption(page, 'Client');
    await selectFirstOption(page, 'Vehicle');

    const tripDate = new Date();
    tripDate.setDate(tripDate.getDate() + 5);
    await page.getByLabel('Trip Date').fill(tripDate.toISOString().split('T')[0]);
    await page.getByLabel('Number of Passengers').fill('30');
    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('San Jose, CA');
    await page.getByLabel('Estimated Miles').fill('50');

    await page.getByRole('button', { name: /create charter/i }).click();
    await page.waitForURL(/.*\/charters\/\d+/, { timeout: 10000 });

    const charterIdMatch = page.url().match(/charters\/(\d+)/);
    if (charterIdMatch) {
      const headers = await getAdminAuthHeaders(request);
      const response = await request.get(
        `${KONG_BASE_URL}/api/v1/charters/${charterIdMatch[1]}`,
        { headers }
      );
      expect(response.ok()).toBeTruthy();
      const charterData = await response.json();
      expect(charterData.total_cost).toBeGreaterThan(0);
    } else {
      throw new Error('Charter ID not found in URL after creation')
    }
  });
});
