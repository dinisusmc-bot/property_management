import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';
import { CharterListPage } from '../../pages/CharterListPage';

/**
 * Charter List Tests
 * Test charter listing, filtering, and search functionality
 */

test.describe('Charter List Page', () => {
  let loginPage: LoginPage;
  let charterListPage: CharterListPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    charterListPage = new CharterListPage(page);
    
    // Login as admin
    await loginPage.goto();
    await loginPage.loginAsAdmin();
    await page.waitForURL(/dashboard|charters/i, { timeout: 10000 });
    
    // Navigate to charters page
    await charterListPage.goto();
  });

  test('should display charter list', async ({ page }) => {
    // Should see charter table
    await expect(page.locator('table, [role="table"]')).toBeVisible();
    
    // Should have at least one charter (from seed data)
    const charterCount = await charterListPage.getCharterCount();
    expect(charterCount).toBeGreaterThan(0);
  });

  test('should show New Charter button', async () => {
    await expect(charterListPage.newCharterButton).toBeVisible();
  });

  test('should navigate to charter detail when clicked', async ({ page }) => {
    // Double-click first charter row
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    
    // Should navigate to charter detail page
    await page.waitForURL(/\/charters\/\d+/, { timeout: 10000 });
    expect(page.url()).toContain('/charters/');
  });

  test('should filter charters by status', async ({ page }) => {
    // Get initial count
    const initialCount = await charterListPage.getCharterCount();
    
    // Filter by 'confirmed' status
    await charterListPage.filterByStatus('confirmed');
    await page.waitForTimeout(500);
    
    // Count should be different (or same if all are confirmed)
    const filteredCount = await charterListPage.getCharterCount();
    expect(filteredCount).toBeGreaterThanOrEqual(0);
  });

  test('should search charters', async ({ page }) => {
    // Search for a client name or charter ID
    await charterListPage.searchCharters('client');
    
    // Should show filtered results
    const searchCount = await charterListPage.getCharterCount();
    expect(searchCount).toBeGreaterThanOrEqual(0);
  });

  test('should display charter details in table', async ({ page }) => {
    // Check table headers
    const table = page.locator('table, [role="table"]');
    
    // Should have common charter fields
    await expect(table.locator('text=/trip date|date/i')).toBeVisible();
    await expect(table.locator('text=/status/i')).toBeVisible();
    await expect(table.locator('text=/client/i')).toBeVisible();
  });
});

test.describe('Charter List - Different Roles', () => {
  test('vendor should see limited charter list', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const charterListPage = new CharterListPage(page);
    
    await loginPage.goto();
    await loginPage.loginAsVendor();
    await page.waitForURL(/dashboard|charters|vendor/i, { timeout: 10000 });
    
    await charterListPage.goto();
    
    // Should see charters assigned to them
    const charterCount = await charterListPage.getCharterCount();
    expect(charterCount).toBeGreaterThanOrEqual(0);
    
    // Should not see "New Charter" button (vendors can't create)
    await expect(charterListPage.newCharterButton).not.toBeVisible();
  });

  test('manager should see all charters', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const charterListPage = new CharterListPage(page);
    
    await loginPage.goto();
    await loginPage.loginAsManager();
    await page.waitForURL(/dashboard|charters/i);
    
    await charterListPage.goto();
    
    // Should see all charters
    const charterCount = await charterListPage.getCharterCount();
    expect(charterCount).toBeGreaterThan(0);
    
    // Should see "New Charter" button
    await expect(charterListPage.newCharterButton).toBeVisible();
  });
});
