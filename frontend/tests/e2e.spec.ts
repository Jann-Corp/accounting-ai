import { test, expect } from '@playwright/test'

const BASE_URL = 'http://localhost:3000'

test.describe('AI记账小程序 - E2E测试', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
  })

  test('未登录访问首页应跳转到登录页', async ({ page }) => {
    await page.goto(BASE_URL)
    await expect(page).toHaveURL(/\/login/)
    await expect(page.locator('h1')).toContainText('AI记账')
  })

  test('登录页面显示正确', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await expect(page.locator('h1')).toContainText('AI记账')
    await expect(page.locator('input[placeholder*="用户名"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toContainText('登录')
  })

  test('注册新用户并登录', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)

    // Click register toggle
    await page.locator('button', { hasText: '立即注册' }).click()
    await expect(page.locator('input[placeholder*="邮箱"]')).toBeVisible()

    // Fill registration form
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `user${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]', `user${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')

    // Submit
    await page.locator('button[type="submit"]').click()

    // Should redirect to home
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })
    await expect(page).not.toHaveURL(/\/login/)
  })

  test('注册重复用户名显示错误', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await page.locator('button', { hasText: '立即注册' }).click()

    await page.fill('input[placeholder*="用户名"]', 'testuser')
    await page.fill('input[placeholder*="邮箱"]', 'another@test.com')
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()

    await expect(page.locator('text=用户名已存在')).toBeVisible({ timeout: 3000 })
  })

  test('登录后显示首页仪表盘', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)

    // Use an existing user from registration flow
    // Register first
    await page.locator('button', { hasText: '立即注册' }).click()
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `dashuser${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]', `dash${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()

    // Wait for redirect to home
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })

    // Check dashboard elements
    await expect(page.locator('text=我的账户')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('text=总资产')).toBeVisible()
  })

  test('侧边栏导航可用', async ({ page }) => {
    // Register and login first
    await page.goto(`${BASE_URL}/login`)
    await page.locator('button', { hasText: '立即注册' }).click()
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `navuser${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]', `nav${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })

    // Navigate to wallets
    await page.locator('a[href="/wallets"]').click()
    await expect(page.locator('h1')).toContainText('账户管理')

    // Navigate to categories
    await page.locator('a[href="/categories"]').click()
    await expect(page.locator('h1')).toContainText('分类管理')

    // Navigate to stats
    await page.locator('a[href="/stats"]').click()
    await expect(page.locator('h1')).toContainText('统计报表')

    // Navigate to records
    await page.locator('a[href="/records"]').click()
    await expect(page.locator('h1')).toContainText('记账记录')

    // Navigate to upload
    await page.locator('a[href="/upload"]').click()
    await expect(page.locator('h1')).toContainText('AI 识别记账')
  })

  test('添加账户', async ({ page }) => {
    // Register and login
    await page.goto(`${BASE_URL}/login`)
    await page.locator('button', { hasText: '立即注册' }).click()
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `walletuser${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]', `wallet${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })

    // Go to wallets page
    await page.locator('a[href="/wallets"]').click()
    await page.locator('button', { hasText: '添加账户' }).click()

    // Fill wallet form
    await page.fill('input[placeholder*="账户名称"]', '我的银行卡')
    await page.locator('select').selectOption('bank')
    await page.fill('input[type="number"]', '5000')
    await page.locator('button[type="submit"]').click()

    // Should see the new wallet
    await expect(page.locator('text=我的银行卡')).toBeVisible({ timeout: 3000 })
  })

  test('添加记账记录', async ({ page }) => {
    // Register and login
    await page.goto(`${BASE_URL}/login`)
    await page.locator('button', { hasText: '立即注册' }).click()
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `recorduser${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]', `record${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })

    // Navigate to records
    await page.locator('a[href="/records"]').click()
    await page.locator('button', { hasText: '添加记录' }).click()

    // Fill record form - select expense type
    await page.fill('input[type="number"]', '50.50')
    await page.fill('input[placeholder*="备注"]', '午餐')
    await page.locator('button[type="submit"]').click()

    // Should see the new record
    await expect(page.locator('text=午餐')).toBeVisible({ timeout: 3000 })
  })

  test('登出功能', async ({ page }) => {
    // Register and login
    await page.goto(`${BASE_URL}/login`)
    await page.locator('button', { hasText: '立即注册' }).click()
    const timestamp = Date.now()
    await page.fill('input[placeholder*="用户名"]', `logoutuser${timestamp}`)
    await page.fill('input[placeholder*="邮箱"]`, `logout${timestamp}@test.com`)
    await page.fill('input[type="password"]', 'TestPass123!')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/\/(?!login)/, { timeout: 5000 })

    // Click logout (in mobile header)
    await page.locator('button', { hasText: '🚪' }).click()

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/, { timeout: 3000 })
  })

})
