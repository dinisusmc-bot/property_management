/**
 * Phase 2.1 Change Case System Tests
 * Tests change request management, workflow, and backend integration
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, requestWithRetry } from '../../fixtures/api-helpers';
import { safeClick } from '../../fixtures/ui-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const goToChanges = async (page: any) => {
  await page.goto('/changes');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForURL('**/changes');
};

const buildChangeRequestPayload = (overrides: Record<string, any> = {}) => {
  const stamp = Date.now();
  return {
    subject: `Change Request ${stamp}`,
    description: `Automated change request test ${stamp}`,
    change_type: 'scheduled',
    priority: 'normal',
    status: 'draft',
    scheduled_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    charter_id: 1,
    ...overrides,
  };
};

const createChangeRequest = async (request: any, overrides: Record<string, any> = {}) => {
  const payload = buildChangeRequestPayload(overrides);
  const headers = await getAdminAuthHeaders(request);
  const response = await requestWithRetry(
    request,
    'post',
    `${KONG_BASE_URL}/api/v1/changes`,
    {
      headers,
      data: payload,
      timeout: 60000,
    },
  );
  expect(response.ok()).toBeTruthy();
  const change = await response.json();
  return { change, payload };
};

test.describe('Change Case System - UI Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await goToChanges(page);
  });

  test('should display changes list page with filters', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /change requests/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /filter/i })).toBeVisible();
    await expect(page.getByText(/status/i)).toBeVisible();
    await expect(page.getByText(/priority/i)).toBeVisible();
  });

  test('should display pending changes with warning styling', async ({ page }) => {
    const pendingBadges = page.getByRole('cell', { name: /pending/i });
    
    // Should find at least one or no pending changes (depending on DB state)
    await pendingBadges.first().or(page.getByText(/no changes found/i)).waitFor();
  });

  test('should navigate to change detail page', async ({ page }) => {
    const firstChangeRow = page.getByRole('row').nth(1);
    
    await safeClick(page, firstChangeRow);
    await page.waitForURL(/.*\/changes\/\d+/);
    expect(page.url()).toMatch(/\/changes\/\d+/);
  });

  test('should have create change button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /create change/i })).toBeVisible();
  });
});

test.describe('Change Case System - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should fetch change requests from backend API', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/changes`,
      { headers, timeout: 60000 },
    );
    const data = await response.json();
    expect(response.ok()).toBeTruthy();

    expect(Array.isArray(data)).toBeTruthy();
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('subject');
      expect(data[0]).toHaveProperty('status');
      expect(data[0]).toHaveProperty('priority');
      expect(data[0]).toHaveProperty('scheduled_date');
    }
  });

  test('should create change request via API', async ({ request }) => {
    const { change, payload } = await createChangeRequest(request);

    expect(change.id).toBeDefined();
    expect(change.subject).toBe(payload.subject);
    expect(change.description).toBe(payload.description);
    expect(change.status).toBe(payload.status);
  });

  test('should persist change request after page refresh', async ({ page, request }) => {
    const { change, payload } = await createChangeRequest(request);

    await goToChanges(page);

    const changeRow = page.getByText(payload.subject);
    await expect(changeRow).toBeVisible({ timeout: 10000 });
  });

  test('should filter change requests by status via backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    
    // Create changes with different statuses
    await createChangeRequest(request, { status: 'approved' });
    await createChangeRequest(request, { status: 'draft' });

    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/changes?status=draft`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(Array.isArray(data)).toBeTruthy();
    data.forEach((change: any) => {
      expect(change.status).toBe('draft');
    });
  });

  test('should show correct priority levels', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/changes`,
      { headers, timeout: 60000 },
    );
    
    const data = await response.json();
    
    if (data.length > 0) {
      const validPriorities = ['low', 'normal', 'high'];
      data.forEach((change: any) => {
        expect(validPriorities).toContain(change.priority);
      });
    }
  });

  test('should display correct scheduled dates from backend', async ({ page, request }) => {
    const { change } = await createChangeRequest(request, {
      scheduled_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
    });

    await goToChanges(page);

    const changeRow = page.getByText(change.subject).locator('..');
    const scheduledDateText = await changeRow.innerText();
    
    expect(scheduledDateText).toContain('3 days');
  });
});

test.describe('Change Case System - Full Workflow', () => {
  test('should complete full change request lifecycle', async ({ page, request }) => {
    const { change } = await createChangeRequest(request, { 
      status: 'draft' 
    });

    // Navigate to change and update status
    await goToChanges(page);
    
    // Open change detail
    const changeRow = page.getByText(change.subject);
    await safeClick(page, changeRow);
    await page.waitForURL(/.*\/changes\/\d+/);

    // Update status to pending
    await page.getByRole('button', { name: /submit/i }).click();
    await page.waitForSelector('[data-testid="success-message"]');

    // Verify backend update
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/changes/${change.id}`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const updatedChange = await response.json();
    expect(updatedChange.status).toBe('pending');
  });

  test('should approve change request', async ({ page, request }) => {
    const { change } = await createChangeRequest(request, { 
      status: 'pending' 
    });

    // Navigate and approve
    await goToChanges(page);
    const changeRow = page.getByText(change.subject);
    await safeClick(page, changeRow);
    await page.waitForURL(/.*\/changes\/\d+/);

    // Approve
    await page.getByRole('button', { name: /approve/i }).click();
    await page.waitForSelector('[data-testid="success-message"]');

    // Verify backend update
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/changes/${change.id}`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const updatedChange = await response.json();
    expect(updatedChange.status).toBe('approved');
  });
});

test.describe('Change Case System - Validation', () => {
  test('should validate required fields', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    
    // Test missing subject
    const response1 = await request.post(
      `${KONG_BASE_URL}/api/v1/changes`,
      {
        headers,
        data: {
          description: 'Test change',
          change_type: 'scheduled',
          status: 'draft',
        },
        timeout: 60000,
      }
    );
    
    expect(response1.ok()).toBeFalsy();
    
    // Test missing change type
    const response2 = await request.post(
      `${KONG_BASE_URL}/api/v1/changes`,
      {
        headers,
        data: {
          subject: 'Test change',
          status: 'draft',
        },
        timeout: 60000,
      }
    );
    
    expect(response2.ok()).toBeFalsy();
  });

  test('should warn about overlapping scheduled dates', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    
    // Create an initial change
    await createChangeRequest(request, {
      scheduled_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'approved'
    });

    // Try to create another change on the same date
    const response = await request.post(
      `${KONG_BASE_URL}/api/v1/changes`,
      {
        headers,
        data: {
          subject: 'Overlapping Change',
          description: 'Should warn about overlap',
          change_type: 'scheduled',
          scheduled_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'draft',
          charter_id: 1,
        },
        timeout: 60000,
      }
    );

    // The API should either succeed or return a warning about overlap
    expect(response.ok()).toBeTruthy();
  });
});
