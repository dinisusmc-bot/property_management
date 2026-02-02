import { Page, Locator } from '@playwright/test';

/**
 * Charter Detail Page Object Model
 * Handles charter detail page interactions
 */
export class CharterDetailPage {
  readonly page: Page;
  readonly statusChip: Locator;
  readonly editButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly sendForApprovalButton: Locator;
  readonly vendorBookedButton: Locator;
  readonly sendConfirmationButton: Locator;
  readonly documentUploadButton: Locator;
  readonly driverSelect: Locator;
  readonly vendorSelect: Locator;

  constructor(page: Page) {
    this.page = page;
    this.statusChip = page.locator('.status-chip, [class*="status"]').first();
    this.editButton = page.locator('button:has-text("Edit")');
    this.saveButton = page.locator('button:has-text("Save")');
    this.cancelButton = page.locator('button:has-text("Cancel")');
    this.sendForApprovalButton = page.locator('button:has-text("Send for Approval")');
    this.vendorBookedButton = page.locator('button:has-text("Vendor Booked")');
    this.sendConfirmationButton = page.locator('button:has-text("Send Confirmation")');
    this.documentUploadButton = page.locator('button:has-text("Upload"), input[type="file"]');
    this.driverSelect = page.locator('select[name="driver_id"], [aria-label*="Driver"]');
    this.vendorSelect = page.locator('select[name="vendor_id"], [aria-label*="Vendor"]');
  }

  async goto(charterId: number) {
    await this.page.goto(`/charters/${charterId}`);
  }

  async getStatus(): Promise<string | null> {
    return await this.statusChip.textContent();
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickSave() {
    await this.saveButton.click();
    // Wait for save to complete
    await this.page.waitForTimeout(1000);
  }

  async sendForApproval() {
    await this.sendForApprovalButton.click();
    // Wait for dialog if any
    await this.page.waitForTimeout(500);
  }

  async uploadDocument(filePath: string, documentType: string) {
    // Click upload button to open dialog
    await this.page.click('button:has-text("Upload"), button:has-text("Vendor Booked"), button:has-text("Send for Approval")');
    
    // Upload file
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Select document type if dropdown exists
    const typeSelect = this.page.locator('select[name="document_type"]');
    if (await typeSelect.isVisible()) {
      await typeSelect.selectOption(documentType);
    }
    
    // Click upload/submit button
    await this.page.click('button:has-text("Upload"), button:has-text("Submit")');
    
    // Wait for upload to complete
    await this.page.waitForTimeout(2000);
  }

  async assignDriver(driverName: string) {
    await this.clickEdit();
    await this.driverSelect.selectOption({ label: driverName });
    await this.clickSave();
  }

  async assignVendor(vendorName: string) {
    await this.clickEdit();
    await this.vendorSelect.selectOption({ label: vendorName });
    await this.clickSave();
  }

  async getDriverName(): Promise<string | null> {
    const driverText = await this.page.locator('text=/Driver:/').locator('..').textContent();
    return driverText?.replace('Driver:', '').trim() || null;
  }

  async getVendorName(): Promise<string | null> {
    const vendorText = await this.page.locator('text=/Vendor:/').locator('..').textContent();
    return vendorText?.replace('Vendor:', '').trim() || null;
  }

  async getPricingDetails() {
    return {
      vendorBase: await this.getFieldValue('vendor_base_cost'),
      vendorMileage: await this.getFieldValue('vendor_mileage_cost'),
      vendorFees: await this.getFieldValue('vendor_additional_fees'),
      clientBase: await this.getFieldValue('client_base_charge'),
      clientMileage: await this.getFieldValue('client_mileage_charge'),
      clientFees: await this.getFieldValue('client_additional_fees'),
    };
  }

  private async getFieldValue(fieldName: string): Promise<number> {
    const field = this.page.locator(`[data-field="${fieldName}"], text=/${fieldName}/i`);
    const text = await field.textContent();
    return parseFloat(text?.replace(/[^0-9.-]/g, '') || '0');
  }
}
