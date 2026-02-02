import { Page, Locator } from '@playwright/test';

/**
 * Charter List Page Object Model
 * Handles charter list page interactions
 */
export class CharterListPage {
  readonly page: Page;
  readonly newCharterButton: Locator;
  readonly searchInput: Locator;
  readonly charterRows: Locator;
  readonly statusFilter: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newCharterButton = page.locator('button:has-text("New Charter"), button:has-text("Create Charter"), a:has-text("New Charter"), a:has-text("Create Charter")');
    this.searchInput = page.locator('input[type="search"], input[placeholder*="Search"], label:has-text("Client Name") + div input, input[value*=""]').first();
    this.charterRows = page.locator('table tbody tr, [role="row"]');
    this.statusFilter = page.locator('select[name="status"], label:has-text("Status") + div input, [aria-label*="status"]');
  }

  async goto() {
    await this.page.goto('/charters');
    // Wait for charter list to load
    await this.page.waitForSelector('table tbody tr, [role="row"]', { timeout: 10000 }).catch(() => {});
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForTimeout(500); // Let React hydrate
  }

  async clickNewCharter() {
    await this.newCharterButton.click();
  }

  async searchCharters(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(1000); // Wait for debounce and re-render
  }

  async filterByStatus(status: string) {
    await this.statusFilter.selectOption(status);
    await this.page.waitForTimeout(500); // Wait for filter to apply
  }

  async getCharterCount(): Promise<number> {
    // Wait a bit for rows to be present
    await this.page.waitForTimeout(500);
    return await this.charterRows.count();
  }

  async clickCharterById(charterId: number) {
    // Wait for the link to be present and visible
    await this.page.waitForSelector(`a[href*="/charters/${charterId}"]`, { timeout: 5000 });
    await this.page.click(`a[href*="/charters/${charterId}"]`);
  }

  async getCharterRow(charterId: number) {
    return this.page.locator(`tr:has(a[href*="/charters/${charterId}"])`);
  }
}
