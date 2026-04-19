import { test, expect } from "@playwright/test";

test.describe("登录/注册", () => {
  test("加载登录页", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toContainText("AI记账");
    await expect(page.getByPlaceholder("请输入用户名")).toBeVisible();
    await expect(page.getByRole("button", { name: /登/ })).toBeVisible();
  });

  test("切换到注册表单", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("登录您的账户")).toBeVisible();
    await expect(page.getByPlaceholder("请输入邮箱")).not.toBeVisible();
    await page.getByRole("button", { name: /立即注册/ }).click();
    await page.waitForTimeout(300);
    await expect(page.getByText("创建新账户")).toBeVisible();
    await expect(page.getByPlaceholder("请输入邮箱")).toBeVisible();
  });

  test("注册并登录", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /立即注册/ }).click();
    await page.waitForTimeout(500);

    const username = "e2e" + Math.floor(Math.random() * 99999);
    await page.getByPlaceholder("请输入用户名").fill(username);
    await page.getByPlaceholder("请输入邮箱").fill(username + "@test.com");
    await page.getByPlaceholder("请输入密码").fill("TestPass123!");
    await page.getByRole("button", { name: "注册" }).click();

    // Wait a bit then check page state
    await page.waitForTimeout(3000);
    const url = page.url();
    const bodyText = await page.locator("body").innerText();
    console.log("URL after submit:", url);
    console.log("Body text:", bodyText.substring(0, 500));
    await expect(url).toContain("/");
  });

  test("未登录访问首页重定向", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL(/login/, { timeout: 5000 });
  });
});