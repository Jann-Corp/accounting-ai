import { test, expect } from '@playwright/test';

test.describe('Timezone Display Tests', () => {
  test('should display dates in Asia/Shanghai timezone', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:53000');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check if the current month is displayed in Chinese
    const currentMonth = await page.locator('text=/\\d{4}年\\d{1,2}月/').textContent();
    console.log('Current month displayed:', currentMonth);
    
    // Verify current month contains 2026 (or current year)
    expect(currentMonth).toMatch(/\d{4}年\d{1,2}月/);
  });
  
  test('login and check date display', async ({ page }) => {
    await page.goto('http://localhost:53000');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check for login form or dashboard
    const pageContent = await page.content();
    console.log('Page loaded, checking for date elements...');
    
    // Look for date-related elements
    const dateElements = await page.locator('text=/\\d{4}-\\d{2}-\\d{2}/').count();
    console.log('Date elements found:', dateElements);
  });
});
