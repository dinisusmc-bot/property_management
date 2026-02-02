import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Athena Charter Management System
 * E2E testing setup with multiple browsers and configurations
 */
export default defineConfig({
  testDir: './tests',
  
  /* Maximum time one test can run for - increased for React SPA loading */
  timeout: 90 * 1000,
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry flaky tests for better reliability */
  retries: process.env.CI ? 2 : 1,
  
  /* Use 36 workers for parallel testing (full CPU utilization) */
  workers: process.env.CI ? 1 : 36,
  
  /* Global timeout for the entire test run */
  globalTimeout: 30 * 60 * 1000,
  
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],
  
  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://localhost:3000',
    
    /* Navigation timeout for SPAs - increased for high worker counts */
    navigationTimeout: 90 * 1000,
    
    /* Action timeout - increased for stability */
    actionTimeout: 20 * 1000,
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video on failure */
    video: 'retain-on-failure',
    
    /* Viewport size */
    viewport: { width: 1280, height: 720 },
    
    /* Ignore HTTPS errors for local development */
    ignoreHTTPSErrors: true,
    
    /* Wait for fonts and images */
    waitForLoadState: 'domcontentloaded',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        /* Chromium-specific launch options for Pop!_OS stability */
        launchOptions: {
          args: [
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-seccomp-filter-sandbox',
          ],
        },
      },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports */
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
        /* Chrome-based mobile also needs these flags */
        launchOptions: {
          args: [
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-seccomp-filter-sandbox',
          ],
        },
      },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Test driver dashboard on mobile (most common use case) */
    {
      name: 'Mobile Driver Dashboard',
      use: { 
        ...devices['iPhone 12'],
        baseURL: 'http://localhost:3000/driver',
        /* This uses webkit (Mobile Safari) so no chromium flags */
      },
      testMatch: '**/tests/drivers/**/*.spec.ts',
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'echo "Using existing services - make sure ./start-all.sh is running"',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
