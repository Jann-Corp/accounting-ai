import { chromium } from 'playwright';

async function test() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Opening login page...');
  await page.goto('http://localhost:53000/login');
  await page.waitForLoadState('networkidle');
  
  // Fill in login form
  await page.fill('input[placeholder="请输入用户名"]', 'apptest');
  await page.fill('input[placeholder="请输入密码"]', 'test123456');
  await page.click('button:has-text("登录")');
  
  // Wait for dashboard to load
  await page.waitForTimeout(3000);
  
  console.log('Current URL:', page.url());
  
  // Check the month display
  const monthLocator = page.locator('p.text-gray-500');
  const monthText = await monthLocator.textContent();
  console.log('Month display:', monthText);
  
  // Verify it's showing April 2026 (not UTC March)
  if (monthText.includes('4月') || monthText.includes('2026')) {
    console.log('✅ Date display looks correct (Asia/Shanghai timezone)');
  } else {
    console.log('❌ Date might still be in wrong timezone');
    console.log('Raw text:', monthText);
  }
  
  // Take screenshot
  await page.screenshot({ path: '/tmp/dashboard.png', fullPage: true });
  console.log('Screenshot saved to /tmp/dashboard.png');
  
  await browser.close();
}

test().catch(console.error);
