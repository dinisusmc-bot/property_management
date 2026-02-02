/**
 * Authentication Helper Functions
 * Shared utilities for logging in as different user roles with proper React SPA waits
 */

import { Page } from '@playwright/test';

/**
 * Login as admin user
 */
export async function loginAsAdmin(page: Page) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  
  // Get element references first (Material-UI uses type attributes, not name)
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.locator('button[type="submit"]');
  
  // Wait for form to be ready
  await emailInput.waitFor({ state: 'visible', timeout: 30000 });
  
  // Fill and submit
  await emailInput.fill('admin@athena.com');
  await passwordInput.fill('admin123');
  await submitButton.click();
  
  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Login as manager user
 */
export async function loginAsManager(page: Page) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.locator('button[type="submit"]');
  
  await emailInput.waitFor({ state: 'visible', timeout: 30000 });
  await emailInput.fill('manager@athena.com');
  await passwordInput.fill('admin123');
  await submitButton.click();
  
  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Login as vendor user
 */
export async function loginAsVendor(page: Page) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.locator('button[type="submit"]');
  
  await emailInput.waitFor({ state: 'visible', timeout: 30000 });
  await emailInput.fill('vendor1@athena.com');
  await passwordInput.fill('admin123');
  await submitButton.click();
  
  // Wait for redirect to vendor page
  await page.waitForURL('**/vendor', { timeout: 10000 });
}

/**
 * Login as driver user
 */
export async function loginAsDriver(page: Page) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.locator('button[type="submit"]');
  
  await emailInput.waitFor({ state: 'visible', timeout: 30000 });
  await emailInput.fill('driver1@athena.com');
  await passwordInput.fill('admin123');
  await submitButton.click();
  
  // Wait for redirect to driver dashboard
  await page.waitForURL('**/driver', { timeout: 10000 });
}
