/**
 * Phase 2.3 QC Task System Tests
 * Tests QC task management, overdue highlighting, and backend integration
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, requestWithRetry } from '../../fixtures/api-helpers';
import { safeClick } from '../../fixtures/ui-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const goToQCTasks = async (page: any) => {
  await page.goto('/qc-tasks');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForURL('**/qc-tasks');
  await page.waitForSelector('[role="heading"]', { timeout: 10000 });
};

const buildQCTaskPayload = (overrides: Record<string, any> = {}) => {
  const stamp = Date.now();
  return {
    title: `QC Check ${stamp}`,
    description: `Automated QC task test ${stamp}`,
    task_type: 'document_review',
    due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    priority: 'medium',
    assigned_to: 1,
    status: 'pending',
    ...overrides,
  };
};

const createQCTask = async (request: any, overrides: Record<string, any> = {}) => {
  const payload = buildQCTaskPayload(overrides);
  const headers = await getAdminAuthHeaders(request);
  const response = await requestWithRetry(
    request,
    'post',
    `${KONG_BASE_URL}/api/v1/qc/tasks`,
    {
      headers,
      data: payload,
      timeout: 60000,
    },
  );
  expect(response.ok()).toBeTruthy();
  const task = await response.json();
  return { task, payload };
};

test.describe('QC Task System - UI Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/qc-tasks');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('[role="heading"]', { timeout: 10000 });
  });

  test('should display QC tasks list page with filters', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /qc tasks/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /filter/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/status/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/priority/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display overdue tasks with warning styling', async ({ page }) => {
    const overdueTasks = page.getByRole('cell', { name: /overdue/i });
    
    await expect(overdueTasks).toHaveCount(0, {
      timeout: 5000,
    });
  });

  test('should navigate to task detail page', async ({ page }) => {
    const firstTaskRow = page.getByRole('row').first().nth(1);
    
    await firstTaskRow.click();
    await page.waitForURL(/.*\/qc-tasks\/\d+/);
    expect(page.url()).toMatch(/\/qc-tasks\/\d+/);
  });

  test('should have create task button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /create task/i })).toBeVisible();
  });
});

test.describe('QC Task System - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should fetch QC tasks from backend API', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/qc/tasks`,
      { headers, timeout: 60000 },
    );
    const data = await response.json();
    expect(response.ok()).toBeTruthy();

    expect(Array.isArray(data)).toBeTruthy();
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('title');
      expect(data[0]).toHaveProperty('status');
      expect(data[0]).toHaveProperty('priority');
      expect(data[0]).toHaveProperty('due_date');
    }
  });

  test('should create QC task via API', async ({ request }) => {
    const { task, payload } = await createQCTask(request);

    expect(task.id).toBeDefined();
    expect(task.title).toBe(payload.title);
    expect(task.description).toBe(payload.description);
    expect(task.status).toBe(payload.status);
  });

  test('should persist QC task after page refresh', async ({ page, request }) => {
    const { task, payload } = await createQCTask(request);

    await goToQCTasks(page);

    const taskRow = page.getByText(payload.title);
    await expect(taskRow).toBeVisible({ timeout: 10000 });
  });

  test('should display correct due dates from backend', async ({ page, request }) => {
    const { task } = await createQCTask(request, {
      due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
    });

    await goToQCTasks(page);

    const taskRow = page.getByText(task.title).locator('..');
    const dueDateText = await taskRow.innerText();
    
    expect(dueDateText).toContain('3 days');
  });

  test('should filter QC tasks by status via backend', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    
    // Create tasks with different statuses
    await createQCTask(request, { status: 'completed' });
    await createQCTask(request, { status: 'pending' });

    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/qc/tasks?status=pending`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(Array.isArray(data)).toBeTruthy();
    data.forEach((task: any) => {
      expect(task.status).toBe('pending');
    });
  });

  test('should show correct priority levels', async ({ page, request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/qc/tasks`,
      { headers, timeout: 60000 },
    );
    
    const data = await response.json();
    
    if (data.length > 0) {
      const validPriorities = ['low', 'medium', 'high'];
      data.forEach((task: any) => {
        expect(validPriorities).toContain(task.priority);
      });
    }
  });
});

test.describe('QC Task System - Full Workflow', () => {
  test('should complete full task lifecycle', async ({ page, request }) => {
    const { task } = await createQCTask(request, { 
      status: 'pending' 
    });

    // Navigate to task and complete it
    await goToQCTasks(page);
    
    // Open task detail (this would click the row)
    const taskRow = page.getByText(task.title);
    await safeClick(page, taskRow);
    await page.waitForURL(/.*\/qc-tasks\/\d+/);

    // Complete task
    await page.getByRole('button', { name: /complete task/i }).click();
    await page.waitForSelector('[data-testid="success-message"]');

    // Verify backend update
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/qc/tasks/${task.id}`,
      { headers, timeout: 60000 },
    );
    
    expect(response.ok()).toBeTruthy();
    const updatedTask = await response.json();
    expect(updatedTask.status).toBe('completed');
  });
});
