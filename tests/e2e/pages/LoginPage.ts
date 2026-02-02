import { Page, Locator } from '@playwright/test';

/**
 * Login Page Object Model
 * Handles all login page interactions
 */
export class LoginPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/', { waitUntil: 'domcontentloaded' });
    // Wait for login form to be visible with longer timeout
    await this.page.waitForSelector('input[type="email"], input[name="email"]', { 
      state: 'visible', 
      timeout: 30000 
    });
  }

  async login(email: string, password: string) {
    // Try multiple selector strategies for robustness
    const emailInput = this.page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = this.page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = this.page.locator('button[type="submit"]').first();
    
    // Wait for form to be ready
    await emailInput.waitFor({ state: 'visible', timeout: 20000 });
    
    // Clear and fill with retry logic
    await emailInput.clear();
    await emailInput.fill(email);
    await this.page.waitForTimeout(100); // Small delay for form validation
    
    await passwordInput.clear();
    await passwordInput.fill(password);
    await this.page.waitForTimeout(100);
    
    // Click and wait for navigation
    await Promise.all([
      this.page.waitForLoadState('domcontentloaded'),
      submitButton.click()
    ]);
    
    // Wait a bit for redirect to complete
    await this.page.waitForTimeout(500);
  }

  async loginAsAdmin() {
    await this.goto();
    await this.login('admin@athena.com', 'admin123');
  }

  async loginAsManager() {
    await this.goto();
    await this.login('manager@athena.com', 'admin123');
  }

  async loginAsVendor() {
    await this.goto();
    await this.login('vendor1@athena.com', 'admin123');
  }

  async loginAsDriver() {
    await this.goto();
    await this.login('driver1@athena.com', 'admin123');
  }

  async getErrorMessage(): Promise<string | null> {
    // Material-UI Alert component
    const errorElement = this.page.getByRole('alert');
    if (await errorElement.isVisible()) {
      return await errorElement.textContent();
    }
    return null;
  }
}
