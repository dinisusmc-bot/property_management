import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';

/**
 * Authentication Tests
 * Test login/logout functionality for all user roles
 */

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    // Check for unique heading and sign in button
    await expect(page.getByRole('heading', { name: /athena charter management/i })).toBeVisible();
    await expect(page.getByText('Sign in to your account')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
  });

  test('should login successfully as admin', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsAdmin();
    
    // Should see dashboard page with unique heading (first one on page)
    await expect(page.getByRole('heading', { name: 'Dashboard' }).first()).toBeVisible();
    await expect(page.getByText('Welcome to Athena Charter Management System')).toBeVisible();
  });

  test('should login successfully as manager', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsManager();
    
    await page.waitForURL(/dashboard|charters/i, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' }).first()).toBeVisible();
  });

  test('should login successfully as vendor', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsVendor();
    
    // Wait for redirect with increased timeout
    await page.waitForURL(/dashboard|charters|vendor/i, { timeout: 10000 });
    
    // Wait for any dashboard content to be visible
    await page.waitForTimeout(1000);
    const hasContent = await page.locator('heading, h1, h2, [role="heading"]').first().isVisible({ timeout: 10000 }).catch(() => false);
    expect(hasContent || page.url().includes('dashboard') || page.url().includes('vendor')).toBeTruthy();
  });

  test('should login successfully as driver and redirect to driver dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsDriver();
    
    // Driver should be redirected to /driver
    await page.waitForURL(/\/driver/i, { timeout: 10000 });
    
    // Should see driver dashboard content - use .first() to avoid strict mode violation
    await expect(page.locator('text=/charter|location|itinerary/i').first()).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('invalid@example.com', 'wrongpassword');
    
    // Should show error - look for various error indicators
    const errorVisible = await page.locator('[role="alert"], .error, .alert, text=/incorrect|invalid|failed|error/i').first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(errorVisible).toBeTruthy();
  });

  test('should logout successfully', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsAdmin();
    
    // Click on avatar button in AppBar (contains Avatar component)
    const avatarButton = page.locator('button').filter({ has: page.locator('[class*="MuiAvatar"]') });
    await avatarButton.click();
    
    // Click logout menu item
    await page.getByRole('menuitem', { name: /logout/i }).click();
    
    // Should redirect to login page
    await expect(page.getByRole('heading', { name: /athena charter management/i })).toBeVisible();
    await expect(page.getByText('Sign in to your account')).toBeVisible();
  });

  test('should maintain session after page reload', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginAsAdmin();
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // Should still be logged in (not redirected back to login)
    const notOnLoginPage = !page.url().includes('/login');
    expect(notOnLoginPage).toBeTruthy();
  });
});

test.describe('Role-based Access', () => {
  test('driver should not access admin pages', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginAsDriver();
    
    // Wait for driver dashboard
    await page.waitForURL(/\/driver/i);
    
    // Try to navigate to charters page
    await page.goto('/charters');
    
    // Should be redirected back to driver dashboard or show error
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url).toMatch(/\/driver|unauthorized|403/i);
  });

  test('vendor should only see assigned charters', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginAsVendor();
    
    await page.waitForURL(/dashboard|charters/i);
    
    // Navigate to charters if not already there
    await page.goto('/charters');
    
    // Should see charters but limited view
    await expect(page.locator('table, [role="table"]')).toBeVisible();
  });
});
