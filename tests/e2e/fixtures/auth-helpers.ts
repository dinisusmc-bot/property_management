/**
 * Authentication Helper Functions
 * Shared utilities for logging in as different user roles with proper React SPA waits
 */

import { Page, expect } from '@playwright/test';

const LOGIN_TIMEOUT = 90000;

const login = async (page: Page, email: string, password: string, redirectUrl: string) => {
  await page.goto('/login', { waitUntil: 'networkidle' });

  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.locator('button[type="submit"]');

  await emailInput.waitFor({ state: 'visible', timeout: LOGIN_TIMEOUT });
  await passwordInput.waitFor({ state: 'visible', timeout: LOGIN_TIMEOUT });
  await submitButton.waitFor({ state: 'visible', timeout: LOGIN_TIMEOUT });
  await expect(submitButton).toBeEnabled({ timeout: LOGIN_TIMEOUT });

  await emailInput.fill(email);
  await passwordInput.fill(password);

  await Promise.all([
    page.waitForURL((url) => !url.pathname.endsWith('/login'), { timeout: LOGIN_TIMEOUT }),
    submitButton.click(),
  ]);

  await page.waitForURL(redirectUrl, { timeout: LOGIN_TIMEOUT }).catch(() => undefined);

  await page.waitForLoadState('networkidle');
};

/**
 * Login as admin user
 */
export async function loginAsAdmin(page: Page) {
  await login(page, 'admin@athena.com', 'admin123', '**/dashboard');
}

/**
 * Login as manager user
 */
export async function loginAsManager(page: Page) {
  await login(page, 'manager@athena.com', 'admin123', '**/dashboard');
}

/**
 * Login as vendor user
 */
export async function loginAsVendor(page: Page) {
  await login(page, 'vendor1@athena.com', 'admin123', '**/vendor');
}

/**
 * Login as driver user
 */
export async function loginAsDriver(page: Page) {
  await login(page, 'driver1@athena.com', 'admin123', '**/driver');
}
