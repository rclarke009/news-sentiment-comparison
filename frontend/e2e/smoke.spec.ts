import { test, expect } from '@playwright/test';

test('frontend loads and shows app content', async ({ page }) => {
  await page.goto('/');
  
  // Wait for something that appears whether we have data or not:
  // - "News Sentiment" (or your header text), or
  // - "No data available" / "Showing latest" / the date picker / etc.
  await expect(page.getByRole('heading', { name: /news senti/i })).toBeVisible({ timeout: 15000 });
  
  // Optional: check we're not stuck on a generic error
  // The app can show: "Loading...", "No Data Available Yet", "Showing latest", or the actual comparison content
  await expect(
    page.getByText(/loading|no data|showing latest|comparison|most uplifting/i)
  ).toBeVisible({ timeout: 10000 });
});
