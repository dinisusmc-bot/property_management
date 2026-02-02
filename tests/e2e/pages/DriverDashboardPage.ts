import { Page, Locator } from '@playwright/test';

/**
 * Driver Dashboard Page Object Model
 * Handles driver dashboard interactions (mobile-optimized)
 */
export class DriverDashboardPage {
  readonly page: Page;
  readonly charterDetailsCard: Locator;
  readonly locationTrackingCard: Locator;
  readonly startTrackingButton: Locator;
  readonly stopTrackingButton: Locator;
  readonly currentLocation: Locator;
  readonly itinerarySection: Locator;
  readonly driverNotesTextarea: Locator;
  readonly saveNotesButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.charterDetailsCard = page.locator('[class*="charter-details"], h2:has-text("Charter Details")').locator('..');
    this.locationTrackingCard = page.locator('[class*="location"], h2:has-text("Location")').locator('..');
    this.startTrackingButton = page.locator('button:has-text("Start Tracking")');
    this.stopTrackingButton = page.locator('button:has-text("Stop Tracking")');
    this.currentLocation = page.locator('text=/Latitude:|Longitude:/');
    this.itinerarySection = page.locator('[class*="itinerary"], h2:has-text("Itinerary")').locator('..');
    this.driverNotesTextarea = page.locator('textarea[name="vendor_notes"], textarea[placeholder*="notes"]');
    this.saveNotesButton = page.locator('button:has-text("Save Notes")');
  }

  async goto() {
    await this.page.goto('/driver');
  }

  async startLocationTracking() {
    await this.startTrackingButton.click();
    // Allow time for geolocation permission
    await this.page.waitForTimeout(1000);
  }

  async stopLocationTracking() {
    await this.stopTrackingButton.click();
  }

  async isTrackingActive(): Promise<boolean> {
    return await this.stopTrackingButton.isVisible();
  }

  async getCurrentLocation(): Promise<{ latitude: string; longitude: string } | null> {
    const locationText = await this.currentLocation.textContent();
    if (!locationText) return null;

    const latMatch = locationText.match(/Latitude:\s*([-\d.]+)/);
    const lonMatch = locationText.match(/Longitude:\s*([-\d.]+)/);

    if (latMatch && lonMatch) {
      return {
        latitude: latMatch[1],
        longitude: lonMatch[1],
      };
    }
    return null;
  }

  async updateNotes(notes: string) {
    await this.driverNotesTextarea.fill(notes);
    await this.saveNotesButton.click();
    // Wait for save
    await this.page.waitForTimeout(1000);
  }

  async getCharterDetails() {
    const detailsText = await this.charterDetailsCard.textContent();
    return {
      tripDate: this.extractField(detailsText, 'Trip Date'),
      status: this.extractField(detailsText, 'Status'),
      passengers: this.extractField(detailsText, 'Passengers'),
      vehicle: this.extractField(detailsText, 'Vehicle'),
    };
  }

  async getItineraryStops(): Promise<number> {
    const stops = this.itinerarySection.locator('[class*="stop"], li');
    return await stops.count();
  }

  private extractField(text: string | null, fieldName: string): string | null {
    if (!text) return null;
    const regex = new RegExp(`${fieldName}[:\\s]+(.*?)(?:\n|$)`, 'i');
    const match = text.match(regex);
    return match ? match[1].trim() : null;
  }

  async hasNoSidebar(): Promise<boolean> {
    const sidebar = this.page.locator('nav[class*="sidebar"], aside');
    return !(await sidebar.isVisible());
  }
}
