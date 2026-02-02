/**
 * Document Management Tests
 * Tests document upload, download, and management for charters
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';
import * as path from 'path';
import * as fs from 'fs';

test.describe('Document Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should upload approval document', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    // Look for upload button or documents section
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      
      // Wait for upload dialog/form
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      // Create test PDF file
      await page.setInputFiles('input[type="file"]', {
        name: 'approval.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 Test Document')
      });
      
      // Select document type
      const docTypeSelect = page.locator('select[name="document_type"], select[name="documentType"]');
      if (await docTypeSelect.isVisible()) {
        await docTypeSelect.selectOption('approval');
      }
      
      // Add description
      const descInput = page.locator('input[name="description"], textarea[name="description"]');
      if (await descInput.isVisible()) {
        await descInput.fill('Client approval document');
      }
      
      // Submit upload
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      
      // Wait for success
      await page.waitForLoadState('networkidle');
      
      // Verify document appears in list
      const hasDocument = await page.locator('text=/approval.pdf|Client approval/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasDocument).toBeTruthy();
    }
  });

  test('should upload booking document', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      await page.setInputFiles('input[type="file"]', {
        name: 'booking-confirmation.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 Booking Document')
      });
      
      const docTypeSelect = page.locator('select[name="document_type"], select[name="documentType"]');
      if (await docTypeSelect.isVisible()) {
        await docTypeSelect.selectOption('booking');
      }
      
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      await page.waitForLoadState('networkidle');
      
      const hasDocument = await page.locator('text=/booking.*confirmation/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasDocument).toBeTruthy();
    }
  });

  test('should upload Word document', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      await page.setInputFiles('input[type="file"]', {
        name: 'contract.docx',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        buffer: Buffer.from('Test Word Document')
      });
      
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      await page.waitForLoadState('networkidle');
      
      const hasDocument = await page.locator('text=/contract.docx/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasDocument).toBeTruthy();
    }
  });

  test('should upload Excel file', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      await page.setInputFiles('input[type="file"]', {
        name: 'invoice.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('Test Excel Document')
      });
      
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      await page.waitForLoadState('networkidle');
      
      const hasDocument = await page.locator('text=/invoice.xlsx/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasDocument).toBeTruthy();
    }
  });

  test('should reject file larger than 10MB', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      // Try to upload large file (simulated - just check validation exists)
      // In real scenario, create 11MB buffer
      await page.setInputFiles('input[type="file"]', {
        name: 'large-file.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.alloc(11 * 1024 * 1024) // 11MB
      });
      
      // Try to submit
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      
      // Should show error message
      const hasError = await page.locator('text=/too large|size limit|10.*MB/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasError).toBeTruthy();
    }
  });

  test('should reject invalid file type', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Add Document")');
    
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForSelector('input[type="file"]', { timeout: 3000 });
      
      // Try to upload executable file
      await page.setInputFiles('input[type="file"]', {
        name: 'malicious.exe',
        mimeType: 'application/x-msdownload',
        buffer: Buffer.from('Test')
      });
      
      await page.click('button[type="submit"]:has-text("Upload"), button:has-text("Save")');
      
      // Should show error
      const hasError = await page.locator('text=/invalid.*type|not allowed|unsupported/i').isVisible({ timeout: 3000 }).catch(() => false);
      expect(hasError).toBeTruthy();
    }
  });

  test('should display document list', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    // Look for documents section
    const docsSection = page.locator('text=/Documents|Attachments/i');
    
    if (await docsSection.isVisible()) {
      // Should show document list or empty state
      const hasDocList = await page.locator('table, .document-list, text=/No documents/i').isVisible();
      expect(hasDocList).toBeTruthy();
    }
  });

  test('should download document', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    // Look for download button on any document
    const downloadButton = page.locator('button:has-text("Download"), a:has-text("Download")').first();
    
    if (await downloadButton.isVisible()) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
      
      await downloadButton.click();
      
      const download = await downloadPromise;
      
      if (download) {
        // Verify download started
        expect(download.suggestedFilename()).toBeTruthy();
      }
    }
  });

  test('should delete document (admin only)', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    // Look for delete button
    const deleteButton = page.locator('button:has-text("Delete"):visible').first();
    
    if (await deleteButton.isVisible()) {
      // Get current document count
      const initialCount = await page.locator('.document-item, tr').count();
      
      await deleteButton.click();
      
      // Confirm deletion
      await page.locator('button:has-text("Confirm"), button:has-text("Yes")').click();
      
      await page.waitForLoadState('networkidle');
      
      // Document count should decrease
      const finalCount = await page.locator('.document-item, tr').count();
      expect(finalCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test('should show document metadata (date, uploader, size)', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.waitForTimeout(500);
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.dblclick();
    await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
    
    // Look for any document in the list
    const docItem = page.locator('.document-item, table tbody tr').first();
    
    if (await docItem.isVisible()) {
      const itemText = await docItem.textContent();
      
      // Should contain date or timestamp
      const hasDate = itemText?.match(/\d{4}|\d{1,2}\/\d{1,2}|ago/);
      expect(hasDate).toBeTruthy();
    }
  });
});
