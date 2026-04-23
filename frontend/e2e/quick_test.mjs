import { chromium } from 'playwright';

async function test() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Opening login page...');
  await page.goto('http://localhost:53000/login');
  await page.waitForLoadState('networkidle');
  
  // Fill in login form
  await page.fill('input[placeholder="请输入用户名"]', 'mktest');
  await page.fill('input[placeholder="请输入密码"]', 'test123456');
  
  console.log('Clicking login button...');
  await page.click('button:has-text("登录")');
  
  // Wait for navigation
  await page.waitForTimeout(3000);
  
  console.log('Current URL:', page.url());
  
  // Take screenshot
  await page.screenshot({ path: '/tmp/login_result.png' });
  console.log('Screenshot saved to /tmp/login_result.png');
  
  // Check if we're on the home page
  if (page.url().includes('login')) {
    console.log('Login might have failed, checking page content...');
    const content = await page.content();
    if (content.includes('错误') || content.includes('失败')) {
      console.log('Login error detected');
    }
  } else {
    console.log('Login successful!');
    
    // Check the date display
    const monthText = await page.textContent('p.text-gray-500');
    console.log('Month display:', monthText);
  }
  
  await browser.close();
}

test().catch(console.error);
