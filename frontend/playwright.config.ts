import { defineConfig, devices } from '@playwright/test';

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      // #can we add safari or other browsers?
      // #yes, we can add safari or other browsers.
      // #we can add safari or other browsers by adding the following to the projects array:
      // #use: { ...devices['Desktop Safari'] },
      // #use: { ...devices['Desktop Firefox'] },
      // #use: { ...devices['Desktop Edge'] },
      // #use: { ...devices['Desktop Opera'] },
      // #use: { ...devices['Desktop Internet Explorer'] },
      // #use: { ...devices['Desktop Microsoft Edge'] },
      // #use: { ...devices['Desktop Microsoft Internet Explorer'] },
      // #use: { ...devices['Desktop Microsoft Edge'] },
      // #use: { ...devices['Desktop Microsoft Internet Explorer'] },
      // #use: { ...devices['Desktop Microsoft Edge'] },
      // #but we are not testing how it looks, just that it loads and shows content?
      // #yes, we are not testing how it looks, just that it loads and shows content.
      
    },
  ],

  /* Run your local dev server before starting the tests */
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  // },
});
