/**
 * Charter Cloning & Templates Tests - Phase 1 Week 4
 * Tests charter cloning, recurring schedules, and template management
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, ensureCharter } from '../../fixtures/api-helpers';
import { safeClick } from '../../fixtures/ui-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const goToFirstCharter = async (page: any, request: any) => {
  const charter = await ensureCharter(request);
  await page.goto(`/charters/${charter.id}`);
  await page.waitForLoadState('networkidle');
  await page.waitForURL(/.*\/charters\/\d+/, { timeout: 10000 });
};

test.describe('Charter Cloning - Single Charter', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should display clone button on charter detail page', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await expect(page.getByRole('button', { name: /clone/i })).toBeVisible();
  });

  test('should open clone dialog when clone button is clicked', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /clone/i }));
    await expect(page.getByRole('dialog', { name: /clone charter/i })).toBeVisible();
    await expect(page.getByLabel('New Trip Date')).toBeVisible();
  });

  test('should clone charter to new date', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /clone/i }));

    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 14);
    await page.getByLabel('New Trip Date').fill(futureDate.toISOString().split('T')[0]);

    await safeClick(page.getByRole('button', { name: /clone charter/i }));
    await expect(page.getByRole('dialog', { name: /clone charter/i })).toBeHidden({ timeout: 10000 });
  });

  test('should cancel clone operation', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /clone/i }));
    await safeClick(page.getByRole('button', { name: /cancel/i }));
    await expect(page.getByRole('dialog', { name: /clone charter/i })).toBeHidden();
  });
});

test.describe('Charter Cloning - Recurring Schedules', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should display recurring button on charter detail page', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await expect(page.getByRole('button', { name: /recurring/i })).toBeVisible();
  });

  test('should open recurring dialog with pattern options', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /recurring/i }));
    await expect(page.getByRole('dialog', { name: /create recurring charters/i })).toBeVisible();
    await expect(page.getByText('Recurrence Pattern')).toBeVisible();
    await expect(page.getByRole('radio', { name: /daily/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: /weekly/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: /monthly/i })).toBeVisible();
  });

  test('should create weekly recurring charters', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /recurring/i }));

    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 7);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 21);

    await page.getByLabel('Start Date').fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel('End Date').fill(endDate.toISOString().split('T')[0]);

    await safeClick(page.getByRole('radio', { name: /weekly/i }));
    await safeClick(page.getByRole('button', { name: /mon/i }));

    await safeClick(page.getByRole('button', { name: /create recurring charters/i }));
    await expect(page.getByRole('dialog', { name: /create recurring charters/i })).toBeHidden({ timeout: 10000 });
  });

  test('should display recurring schedule preview', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /recurring/i }));
    await safeClick(page.getByRole('radio', { name: /weekly/i }));
    await safeClick(page.getByRole('button', { name: /mon/i }));

    await expect(page.getByText(/schedule preview/i)).toBeVisible();
    await expect(page.getByText(/every week/i)).toBeVisible();
  });
});

test.describe('Charter Templates - Save and Apply', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should display save as template button', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await expect(page.getByRole('button', { name: /template/i })).toBeVisible();
  });

  test('should open save as template dialog', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /template/i }));
    await expect(page.getByRole('dialog', { name: /save as template/i })).toBeVisible();
    await expect(page.getByLabel('Template Name')).toBeVisible();
  });

  test('should save charter as template', async ({ page, request }) => {
    await goToFirstCharter(page, request);

    await safeClick(page.getByRole('button', { name: /template/i }));

    const uniqueName = `Test Template ${Date.now()}`;
    await page.getByLabel('Template Name').fill(uniqueName);

    await safeClick(page.getByRole('button', { name: /save template/i }));
    await expect(page.getByRole('dialog', { name: /save as template/i })).toBeHidden({ timeout: 10000 });
  });
});

test.describe('Charter Templates - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should persist cloned charter in backend', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    const charter = await ensureCharter(request);

    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 21);
    const cloneResponse = await request.post(`${KONG_BASE_URL}/api/v1/charters/${charter.id}/clone`, {
      headers,
      data: { trip_date: futureDate.toISOString().split('T')[0] },
    });

    expect(cloneResponse.ok()).toBeTruthy();
    const cloneData = await cloneResponse.json();
    expect(cloneData).toHaveProperty('charter_id');

    const verifyResponse = await request.get(`${KONG_BASE_URL}/api/v1/charters/${cloneData.charter_id}`, { headers });
    expect(verifyResponse.ok()).toBeTruthy();
  });

  test('should fetch charter templates from backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await request.get(`${KONG_BASE_URL}/api/v1/charters/templates`, {
      headers,
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('should create recurring charters in backend', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    const charter = await ensureCharter(request);

    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 35);

    const seriesResponse = await request.post(`${KONG_BASE_URL}/api/v1/charters/series`, {
      headers,
      data: {
        series_name: `Test Series ${Date.now()}`,
        client_id: charter.client_id,
        template_charter_id: charter.id,
        recurrence_pattern: 'daily',
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        generate_charters: true,
      },
    });

    expect(seriesResponse.ok()).toBeTruthy();
    const seriesData = await seriesResponse.json();
    expect(seriesData).toHaveProperty('series_id');
    expect(seriesData.charters_created).toBeGreaterThan(0);
  });
});
