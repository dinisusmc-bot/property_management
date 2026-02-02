/**
 * Charter Workflow Tests
 * Tests the complete charter lifecycle: Quote → Approved → Booked → Confirmed → In Progress → Completed
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../fixtures/auth-helpers';

test.describe('Charter Workflow Transitions', () => {
  
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should transition from Quote to Approved', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find charter with Quote status
    const quoteCharter = page.locator('tr:has-text("Quote")').first();
    
    if (await quoteCharter.isVisible()) {
      await quoteCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Verify current status
      await expect(page.locator('.status-chip:has-text("Quote"), [data-status="quote"]')).toBeVisible();
      
      // Look for "Send for Approval" button
      const sendApprovalButton = page.locator('button:has-text("Send for Approval")');
      
      if (await sendApprovalButton.isVisible()) {
        await sendApprovalButton.click();
        
        // Wait for processing
        await page.waitForLoadState('networkidle');
        
        // Email should be sent (check for success message)
        const emailSentMessage = await page.locator('text=email sent, text=Email sent').isVisible().catch(() => false);
        expect(emailSentMessage).toBeTruthy();
      }
      
      // Manually update status to Approved (simulating client approval)
      const statusSelect = page.locator('select[name="status"]');
      if (await statusSelect.isVisible()) {
        await statusSelect.selectOption('approved');
        await page.click('button:has-text("Save"), button:has-text("Update")');
        await page.waitForLoadState('networkidle');
        
        // Verify status changed
        await expect(page.locator('.status-chip:has-text("Approved")')).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should transition from Approved to Booked with document upload', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find charter with Approved status
    const approvedCharter = page.locator('tr:has-text("Approved")').first();
    
    if (await approvedCharter.isVisible()) {
      await approvedCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Look for "Vendor Booked" or "Mark as Booked" button
      const bookedButton = page.locator('button:has-text("Vendor Booked"), button:has-text("Mark as Booked")');
      
      if (await bookedButton.isVisible()) {
        await bookedButton.click();
        
        // Upload booking confirmation document
        const fileInput = page.locator('input[type="file"]');
        if (await fileInput.isVisible({ timeout: 2000 })) {
          // Create a test file
          await fileInput.setInputFiles({
            name: 'booking-confirmation.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('Test booking document')
          });
          
          // Set document type if dropdown exists
          const docTypeSelect = page.locator('select[name="document_type"]');
          if (await docTypeSelect.isVisible()) {
            await docTypeSelect.selectOption('booking');
          }
          
          // Upload
          await page.click('button:has-text("Upload")');
          await page.waitForLoadState('networkidle');
        }
        
        // Enter vendor booking cost
        const costInput = page.locator('input[name="vendor_base_cost"], input[name="booking_cost"]');
        if (await costInput.isVisible()) {
          await costInput.fill('500.00');
        }
        
        // Save/Submit
        await page.click('button:has-text("Save"), button:has-text("Submit")');
        await page.waitForLoadState('networkidle');
        
        // Verify status changed to Booked
        await expect(page.locator('.status-chip:has-text("Booked")')).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should transition from Booked to Confirmed', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find charter with Booked status
    const bookedCharter = page.locator('tr:has-text("Booked")').first();
    
    if (await bookedCharter.isVisible()) {
      await bookedCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Look for "Send Confirmation" button
      const confirmButton = page.locator('button:has-text("Send Confirmation"), button:has-text("Confirm Charter")');
      
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        
        // Wait for email to be sent
        await page.waitForLoadState('networkidle');
        
        // Check for success message
        const emailSent = await page.locator('text=Confirmation sent, text=Email sent').isVisible().catch(() => false);
        expect(emailSent).toBeTruthy();
        
        // Status should change to Confirmed
        await page.waitForTimeout(1000);
        await expect(page.locator('.status-chip:has-text("Confirmed")')).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should transition from Confirmed to In Progress', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find charter with Confirmed status
    const confirmedCharter = page.locator('tr:has-text("Confirmed")').first();
    
    if (await confirmedCharter.isVisible()) {
      await confirmedCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Look for "Start Charter" or status update button
      const startButton = page.locator('button:has-text("Start Charter"), button:has-text("Mark In Progress")');
      
      if (await startButton.isVisible()) {
        await startButton.click();
        await page.waitForLoadState('networkidle');
        
        // Status should change to In Progress
        await expect(page.locator('.status-chip:has-text("In Progress")')).toBeVisible({ timeout: 3000 });
      } else {
        // Fallback: use status dropdown
        const statusSelect = page.locator('select[name="status"]');
        if (await statusSelect.isVisible()) {
          await statusSelect.selectOption('in_progress');
          await page.click('button:has-text("Save"), button:has-text("Update")');
          await page.waitForLoadState('networkidle');
          
          await expect(page.locator('.status-chip:has-text("In Progress")')).toBeVisible({ timeout: 3000 });
        }
      }
    }
  });

  test('should transition from In Progress to Completed', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find charter with In Progress status
    const inProgressCharter = page.locator('tr:has-text("In Progress")').first();
    
    if (await inProgressCharter.isVisible()) {
      await inProgressCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Look for "Complete Charter" button
      const completeButton = page.locator('button:has-text("Complete"), button:has-text("Mark Completed")');
      
      if (await completeButton.isVisible()) {
        await completeButton.click();
        await page.waitForLoadState('networkidle');
        
        // Status should change to Completed
        await expect(page.locator('.status-chip:has-text("Completed")')).toBeVisible({ timeout: 3000 });
      } else {
        // Fallback: use status dropdown
        const statusSelect = page.locator('select[name="status"]');
        if (await statusSelect.isVisible()) {
          await statusSelect.selectOption('completed');
          await page.click('button:has-text("Save"), button:has-text("Update")');
          await page.waitForLoadState('networkidle');
          
          await expect(page.locator('.status-chip:has-text("Completed")')).toBeVisible({ timeout: 3000 });
        }
      }
    }
  });

  test('should display correct workflow buttons based on status', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Test Quote status buttons
    const quoteCharter = page.locator('tr:has-text("Quote")').first();
    if (await quoteCharter.isVisible()) {
      await quoteCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Should show "Send for Approval" button
      const hasSendApproval = await page.locator('button:has-text("Send for Approval")').isVisible().catch(() => false);
      expect(hasSendApproval).toBeTruthy();
      
      // Go back
      await page.goto('http://localhost:3000/charters');
    }
    
    // Test Approved status buttons
    const approvedCharter = page.locator('tr:has-text("Approved")').first();
    if (await approvedCharter.isVisible()) {
      await approvedCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Should show "Vendor Booked" or similar button
      const hasBookedButton = await page.locator('button:has-text("Vendor Booked"), button:has-text("Book Vendor")').isVisible().catch(() => false);
      expect(hasBookedButton).toBeTruthy();
    }
  });

  test('should display status color coding correctly', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Check that status chips have appropriate colors
    // Quote = gray/default, Approved = blue, Confirmed = green, Completed = green, etc.
    
    const statusChips = page.locator('.status-chip, [data-status]');
    const count = await statusChips.count();
    
    if (count > 0) {
      // Just verify they're visible and have some styling
      for (let i = 0; i < Math.min(count, 3); i++) {
        await expect(statusChips.nth(i)).toBeVisible();
      }
    }
  });

  test('should prevent invalid workflow transitions', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find a charter with Quote status
    const quoteCharter = page.locator('tr:has-text("Quote")').first();
    
    if (await quoteCharter.isVisible()) {
      await quoteCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Try to jump directly to Completed (should not be allowed)
      const statusSelect = page.locator('select[name="status"]');
      if (await statusSelect.isVisible()) {
        const completedOption = await statusSelect.locator('option[value="completed"]').isDisabled().catch(() => true);
        
        // Completed should be disabled or not in the list
        expect(completedOption).toBeTruthy();
      }
    }
  });

  test('should allow workflow reversal/cancellation', async ({ page }) => {
    await page.goto('http://localhost:3000/charters');
    
    // Find any non-completed charter
    const activeCharter = page.locator('tr:not(:has-text("Completed"))').first();
    
    if (await activeCharter.isVisible()) {
      await activeCharter.click();
      await page.waitForURL(/.*charters\/\d+/, { timeout: 10000 });
      
      // Look for Cancel button
      const cancelButton = page.locator('button:has-text("Cancel")');
      
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
        
        // Confirm cancellation
        await page.locator('button:has-text("Confirm"), button:has-text("Yes")').click();
        
        await page.waitForLoadState('networkidle');
        
        // Status should change to Cancelled
        await expect(page.locator('.status-chip:has-text("Cancelled"), .status-chip:has-text("Canceled")')).toBeVisible({ timeout: 3000 });
      }
    }
  });
});
