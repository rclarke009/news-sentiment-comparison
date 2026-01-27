import { test, expect } from '@playwright/test';

test('frontend loads and shows app content', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the page to load - give it time for React to mount
  await page.waitForLoadState('domcontentloaded');
  
  // Wait for either:
  // 1. Loading state to appear and then disappear, OR
  // 2. Content to appear directly
  
  // Check if we see "Loading..." - if so, wait for it to disappear
  const loadingLocator = page.getByText(/^loading$/i);
  const isLoading = await loadingLocator.isVisible().catch(() => false);
  
  if (isLoading) {
    // Wait for loading to finish (max 20 seconds)
    await expect(loadingLocator).not.toBeVisible({ timeout: 20000 });
  }
  
  // After loading completes, verify we see meaningful content.
  // Use a flexible text matcher that will match any of the expected states:
  // - "News Sentiment Comparison" (header)
  // - "No Data Available Yet" 
  // - "Showing latest"
  // - "Comparison" or "Most Uplifting" (content)
  
  // Try to find the header first (most reliable indicator)
  const headerText = page.getByText(/news sentiment comparison/i);
  const headerFound = await headerText.isVisible({ timeout: 10000 }).catch(() => false);
  
  if (!headerFound) {
    // If header not found, check for other expected content
    await expect(
      page.getByText(/no data available|showing latest|comparison|most uplifting/i)
    ).toBeVisible({ timeout: 10000 });
  }
});
