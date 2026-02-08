/**
 * Agent Dashboard Tests - Phase 1 Week 3
 * Tests dashboard cards, navigation, and backend data access
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, requestWithRetry } from '../../fixtures/api-helpers';

const KONG_BASE_URL = getKongBaseUrl();

test.describe('Agent Dashboard - Metrics Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard page with key cards', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /sales dashboard/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Sales Performance' })).toBeVisible();
    await expect(page.getByText(/conversion funnel/i)).toBeVisible();
    await expect(page.getByText('Top Performers')).toBeVisible();
    await expect(page.getByText('Recent Activity')).toBeVisible();
    await expect(page.getByText('Quick Actions')).toBeVisible();
  });

  test('should navigate from quick actions to create lead page', async ({ page }) => {
    await page.getByRole('button', { name: /create lead/i }).click();
    await page.waitForURL(/.*\/leads\/new/);
    expect(page.url()).toMatch(/\/leads\/new/);
  });

  test('should navigate from quick actions to create charter page', async ({ page }) => {
    await page.getByRole('button', { name: /create charter/i }).click();
    await page.waitForURL(/.*\/charters\/new/);
    expect(page.url()).toMatch(/\/charters\/new/);
  });
});

test.describe('Agent Dashboard - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should fetch sales metrics from backend API', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/sales/metrics?period=month`,
      { headers, timeout: 60000 },
    );
    const data = await response.json();
    expect(response.ok()).toBeTruthy();

    expect(data).toHaveProperty('total_leads');
    expect(data).toHaveProperty('converted');
    expect(data).toHaveProperty('conversion_rate');
  });

  test('should fetch conversion funnel data from backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/sales/funnel?period=month`,
      { headers, timeout: 60000 },
    );
    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(Array.isArray(data.funnel)).toBeTruthy();
    if (data.funnel.length > 0) {
      expect(data.funnel[0]).toHaveProperty('stage');
      expect(data.funnel[0]).toHaveProperty('count');
    }
  });

  test('should fetch top performers from backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/sales/top-performers?limit=10`,
      { headers, timeout: 60000 },
    );
    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(Array.isArray(data.performers)).toBeTruthy();
  });

  test('should fetch recent activity from backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/sales/activity?limit=10`,
      { headers, timeout: 60000 },
    );
    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(Array.isArray(data.activities)).toBeTruthy();
  });

  test('should display backend metrics on dashboard', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/sales/metrics?period=month`,
      { headers, timeout: 60000 },
    );
    expect(response.ok()).toBeTruthy();
    const backendData = await response.json();

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const formattedTotal = new Intl.NumberFormat('en-US').format(backendData.total_leads);
    const totalLeadsCard = page.getByText('Total Leads').locator('..').locator('..');

    await expect(totalLeadsCard.getByText(new RegExp(`^(${backendData.total_leads}|${formattedTotal})$`))).toBeVisible({
      timeout: 10000,
    });
  });
});
