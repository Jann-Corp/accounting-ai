import { chromium } from 'playwright';

async function test() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Opening login page...');
  await page.goto('http://localhost:53000/login');
  await page.waitForLoadState('networkidle');
  
  // Fill in login form
  console.log('Filling username...');
  await page.fill('input[placeholder="请输入用户名"]', 'apptest');
  
  console.log('Filling password...');
  await page.fill('input[placeholder="请输入密码"]', 'test123456');
  
  console.log('Clicking login button...');
  await page.click('button:has-text("登录")');
  
  // Wait for navigation or error
  await page.waitForTimeout(5000);
  
  console.log('Current URL:', page.url());
  
  // Check for any error messages
  const errorLocator = page.locator('.text-red-500, .text-red-600, [class*="error"]');
  if (await errorLocator.count() > 0) {
    console.log('Error message found:', await errorLocator.first().textContent());
  }
  
  // Check page content
  const content = await page.content();
  if (content.includes('用户名或密码错误')) {
    console.log('Login failed: Wrong username or password');
  } else if (content.includes('记账')) {
    console.log('Login appears successful - found dashboard content');
  }
  
  // Take screenshot
  await page.screenshot({ path: '/tmp/login_result.png', fullPage: true });
  console.log('Screenshot saved to /tmp/login_result.png');
  
  await browser.close();
}

test().catch(console.error);
