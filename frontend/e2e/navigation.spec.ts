import { test, expect } from "@playwright/test";

test.use({ storageState: { cookies: [], origins: [] } });

test.describe("导航", () => {
  let username: string;

  test.beforeEach(async ({ page }) => {
    // Register and login
    username = "nav" + Math.floor(Math.random() * 99999);
    await page.goto("/login");
    await page.getByRole("button", { name: /立即注册/ }).click();
    await page.waitForTimeout(300);
    await page.getByPlaceholder("请输入用户名").fill(username);
    await page.getByPlaceholder("请输入邮箱").fill(username + "@test.com");
    await page.getByPlaceholder("请输入密码").fill("TestPass123!");
    await page.getByRole("button", { name: "注册" }).click();
    await page.waitForURL("http://localhost:3000/", { timeout: 10000 });
  });

  test("侧边栏导航链接", async ({ page }) => {
    // Records
    await page.getByRole("link", { name: /记账/ }).first().click();
    await expect(page).toHaveURL(/records/);

    // Upload
    await page.getByRole("link", { name: /AI/ }).first().click();
    await expect(page).toHaveURL(/upload/);

    // Wallets
    await page.getByRole("link", { name: /账户/ }).first().click();
    await expect(page).toHaveURL(/wallets/);

    // Categories
    await page.getByRole("link", { name: /分类/ }).first().click();
    await expect(page).toHaveURL(/categories/);

    // Stats
    await page.getByRole("link", { name: /统计/ }).first().click();
    await expect(page).toHaveURL(/stats/);

    // Home
    await page.getByRole("link", { name: /首页/ }).first().click();
    await expect(page).toHaveURL(/\/$|\/$/);
  });

  test("创建账户", async ({ page }) => {
    await page.getByRole("link", { name: /账户/ }).first().click();
    await page.waitForURL(/wallets/);
    await page.getByRole("button", { name: "+ 添加账户" }).click();
    await page.waitForTimeout(300);
    await page.getByLabel("账户名称").fill("测试银行卡");
    await page.getByRole("button", { name: "保存" }).click();
    await expect(page.getByText("测试银行卡")).toBeVisible({ timeout: 5000 });
  });
});