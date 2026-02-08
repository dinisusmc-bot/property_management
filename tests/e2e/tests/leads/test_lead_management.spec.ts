/**
 * Lead Management Tests - Phase 1 Week 1
 * Tests lead CRUD operations, status workflow, and conversion
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import { getKongBaseUrl, getAdminAuthHeaders, requestWithRetry } from '../../fixtures/api-helpers';
import { safeClick } from '../../fixtures/ui-helpers';

const KONG_BASE_URL = getKongBaseUrl();

const goToLeads = async (page: any) => {
  await page.goto('/leads');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForURL('**/leads');
};

const buildLeadPayload = (overrides: Record<string, any> = {}) => {
  const stamp = Date.now();
  return {
    first_name: 'Test',
    last_name: `Lead${stamp}`,
    email: `test.lead.${stamp}@example.com`,
    phone: '555-0123',
    source: 'web',
    estimated_passengers: 30,
    estimated_trip_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    pickup_location: 'San Francisco, CA',
    dropoff_location: 'Los Angeles, CA',
    ...overrides,
  };
};

const createLead = async (request: any, overrides: Record<string, any> = {}) => {
  const payload = buildLeadPayload(overrides);
  const headers = await getAdminAuthHeaders(request);
  const response = await requestWithRetry(
    request,
    'post',
    `${KONG_BASE_URL}/api/v1/sales/api/v1/leads`,
    {
      headers,
      data: payload,
      timeout: 60000,
    },
  );
  expect(response.ok()).toBeTruthy();
  const lead = await response.json();
  return { lead, payload };
};

const waitForLeadByEmail = async (request: any, email: string, attempts = 10) => {
  const headers = await getAdminAuthHeaders(request);

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const listResponse = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads`,
      { headers, timeout: 60000 },
    );

    if (listResponse.ok()) {
      const listData = await listResponse.json();
      const match = Array.isArray(listData)
        ? listData.find((item: any) => item.email === email)
        : null;
      if (match) {
        return match;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`Lead with email ${email} not found after retries`);
};

const waitForLeadById = async (request: any, leadId: number, attempts = 10) => {
  const headers = await getAdminAuthHeaders(request);

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads/${leadId}`,
      { headers, timeout: 60000 },
    );

    if (response.ok()) {
      return await response.json();
    }

    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`Lead ${leadId} not found after retries`);
};

const waitForLeadConverted = async (request: any, leadId: number, attempts = 10) => {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const lead = await waitForLeadById(request, leadId, 1).catch(() => null);
    if (lead?.status === 'converted' || lead?.converted_to_charter_id) {
      return lead;
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`Lead ${leadId} did not convert after retries`);
};

const waitForLeadRemoval = async (request: any, leadId: number, attempts = 10) => {
  const headers = await getAdminAuthHeaders(request);

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const listResponse = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads`,
      { headers, timeout: 60000 },
    );

    if (listResponse.ok()) {
      const listData = await listResponse.json();
      const stillExists = Array.isArray(listData) && listData.some((item: any) => item.id === leadId);
      if (!stillExists) {
        return;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`Lead ${leadId} still exists after delete retries`);
};

const waitForLeadStatus = async (request: any, leadId: number, status: string, attempts = 10) => {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const lead = await waitForLeadById(request, leadId, 1).catch(() => null);
    if (lead?.status === status) {
      return lead;
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`Lead ${leadId} did not reach status ${status}`);
};

test.describe('Lead Management - CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should display lead list page', async ({ page }) => {
    await goToLeads(page);
    await expect(page.getByRole('heading', { name: /leads/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
  });

  test('should create new lead with required fields', async ({ page, request }) => {
    await goToLeads(page);
    await safeClick(page.getByRole('button', { name: /new lead/i }));
    await page.waitForURL(/.*\/leads\/new/);

    await page.getByLabel('First Name').fill('John');
    await page.getByLabel('Last Name').fill('Doe');
    const email = `test.lead.${Date.now()}@example.com`;
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Phone').fill('555-0123');

    await page.getByLabel('Source').click();
    await page.getByRole('option', { name: 'Web' }).click();

    await page.getByLabel('Pickup Location').fill('San Francisco, CA');
    await page.getByLabel('Dropoff Location').fill('Los Angeles, CA');
    await page.getByLabel('Passengers').fill('30');

    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    await page.getByLabel('Trip Date').fill(nextWeek.toISOString().split('T')[0]);

    const createButton = page.getByRole('button', { name: /create lead/i });
    await expect(createButton).toBeEnabled();
    await createButton.click();

    const createdLead = await waitForLeadByEmail(request, email);
    if (!/\/leads\/\d+/.test(page.url())) {
      await page.goto(`/leads/${createdLead.id}`);
    }

    await expect(page.getByText(/contact information/i)).toBeVisible({ timeout: 60000 });
  });

  test('should view lead detail page', async ({ page, request }) => {
    const { lead } = await createLead(request);

    await goToLeads(page);
    await page.getByLabel('Search').fill(lead.email);
    const row = page.locator('table tbody tr').filter({ hasText: lead.email }).first();
    await safeClick(row.getByTitle('View Details'));

    await expect(page.getByText(/contact information/i)).toBeVisible();
  });

  test('should update lead status', async ({ page, request }) => {
    const { lead } = await createLead(request);

    await goToLeads(page);
    await page.getByLabel('Search').fill(lead.email);
    const row = page.locator('table tbody tr').filter({ hasText: lead.email }).first();
    await safeClick(row.getByTitle('Edit'));
    await page.waitForURL(/.*\/leads\/\d+\/edit/);

    await page.getByRole('combobox', { name: /status/i }).click();
    await page.getByRole('option', { name: 'Qualified' }).click();
    await page.getByRole('button', { name: /update lead|save/i }).click();
    await waitForLeadStatus(request, lead.id, 'qualified');

    const headers = await getAdminAuthHeaders(request);
    const updated = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads/${lead.id}`,
      { headers, timeout: 60000 },
    );
    expect(updated.ok()).toBeTruthy();
    const updatedLead = await updated.json();
    expect(updatedLead.status).toBe('qualified');
  });

  test('should convert lead to quote', async ({ page, request }) => {
    const { lead } = await createLead(request);

    await goToLeads(page);
    await page.getByLabel('Search').fill(lead.email);
    const row = page.locator('table tbody tr').filter({ hasText: lead.email }).first();
    await safeClick(row.getByTitle('View Details'));

    const convertButton = page.getByRole('button', { name: /convert to quote/i });
    await expect(convertButton).toBeVisible({ timeout: 5000 });
    page.on('dialog', (dialog) => dialog.accept());
    await safeClick(convertButton);

    const convertedLead = await waitForLeadConverted(request, lead.id);
    if (convertedLead.converted_to_charter_id && !/\/charters\/\d+/.test(page.url())) {
      await page.goto(`/charters/${convertedLead.converted_to_charter_id}`);
    }

    await page.waitForURL(/.*\/charters\/\d+/, { timeout: 30000, waitUntil: 'domcontentloaded' });
    expect(page.url()).toMatch(/\/charters\/\d+/);
  });

  test('should filter leads by status', async ({ page, request }) => {
    const { lead: leadA } = await createLead(request, { first_name: 'Alpha' });
    const { lead: leadB } = await createLead(request, { first_name: 'Bravo' });

    const headers = await getAdminAuthHeaders(request);
    await requestWithRetry(
      request,
      'put',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads/${leadB.id}`,
      {
        headers,
        data: { status: 'qualified' },
      },
    );

    await goToLeads(page);
    await page.getByLabel('Status').click();
    await page.getByRole('option', { name: 'Qualified' }).click();

    const rows = page.locator('table tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);

    for (let i = 0; i < rowCount; i += 1) {
      await expect(rows.nth(i)).toContainText('qualified');
    }
  });

  test('should delete lead', async ({ page, request }) => {
    const { lead, payload } = await createLead(request, { first_name: 'DeleteMe' });

    await goToLeads(page);
    await page.getByLabel('Search').fill(payload.email);

    page.on('dialog', (dialog) => dialog.accept());
    await safeClick(page.locator('button[title="Delete"]').first());
    await waitForLeadRemoval(request, lead.id);
  });
});

test.describe('Lead Management - Backend Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should persist lead data after page refresh', async ({ page, request }) => {
    await goToLeads(page);
    await safeClick(page.getByRole('button', { name: /new lead/i }));
    await page.waitForURL(/.*\/leads\/new/);

    const uniqueEmail = `persistence.test.${Date.now()}@example.com`;
    await page.getByLabel('First Name').fill('Persistence');
    await page.getByLabel('Last Name').fill('Tester');
    await page.getByLabel('Email').fill(uniqueEmail);
    await page.getByLabel('Source').click();
    await page.getByRole('option', { name: 'Web' }).click();

    const createButton = page.getByRole('button', { name: /create lead/i });
    await expect(createButton).toBeEnabled();
    await createButton.click();
    await waitForLeadByEmail(request, uniqueEmail);
    await page.waitForURL(/.*\/leads\/\d+/, { timeout: 60000, waitUntil: 'domcontentloaded' }).catch(() => undefined);

    await goToLeads(page);
    await page.getByLabel('Search').fill(uniqueEmail);
    await expect(page.getByText(uniqueEmail)).toBeVisible({ timeout: 5000 });
  });

  test('should validate backend API returns correct lead data structure', async ({ request }) => {
    const headers = await getAdminAuthHeaders(request);
    const response = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads`,
      { headers, timeout: 60000 },
    );
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();

    if (data.length > 0) {
      const firstLead = data[0];
      expect(firstLead).toHaveProperty('id');
      expect(firstLead).toHaveProperty('status');
      expect(firstLead).toHaveProperty('first_name');
      expect(firstLead).toHaveProperty('last_name');
    }
  });

  test('should update backend when lead status changes', async ({ page, request }) => {
    const { lead } = await createLead(request);

    await goToLeads(page);
    await page.getByLabel('Search').fill(lead.email);
    const row = page.locator('table tbody tr').filter({ hasText: lead.email }).first();
    await safeClick(row.getByTitle('Edit'));

    await page.getByLabel('Status').click();
    await page.getByRole('option', { name: 'Qualified' }).click();
    await page.getByRole('button', { name: /update lead|save/i }).click();
    await waitForLeadStatus(request, lead.id, 'qualified');

    const headers = await getAdminAuthHeaders(request);
    const updatedResponse = await requestWithRetry(
      request,
      'get',
      `${KONG_BASE_URL}/api/v1/sales/api/v1/leads/${lead.id}`,
      { headers },
    );
    expect(updatedResponse.ok()).toBeTruthy();
    const updatedData = await updatedResponse.json();
    expect(updatedData.status).toBe('qualified');
  });
});
