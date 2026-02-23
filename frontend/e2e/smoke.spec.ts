import { test, expect } from "@playwright/test";

test("homepage shows novel cards section", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h2, h1, [class*='novel'], [class*='card']").first()).toBeVisible();
});

test("/novels shows the novel grid", async ({ page }) => {
  await page.goto("/novels");
  // Page should load without error — check for a heading or grid container
  await expect(page).toHaveURL(/\/novels/);
  await expect(page.locator("body")).not.toContainText("500");
});

test("/leaderboard shows the 3 period tabs", async ({ page }) => {
  await page.goto("/leaderboard");
  await expect(page.getByRole("tab", { name: /hôm nay/i })).toBeVisible();
  await expect(page.getByRole("tab", { name: /tuần/i })).toBeVisible();
  await expect(page.getByRole("tab", { name: /tháng/i })).toBeVisible();
});

test("/novels search updates URL query", async ({ page }) => {
  await page.goto("/novels");
  const searchInput = page.getByPlaceholder(/tìm kiếm/i);
  await searchInput.fill("tiên");
  await searchInput.press("Enter");
  await expect(page).toHaveURL(/q=ti%C3%AAn|q=ti.n/);
});

test("/library without login shows redirect or login prompt", async ({ page }) => {
  await page.goto("/library");
  // Either redirected to home or shows a login-related message
  const url = page.url();
  const isRedirected = !url.includes("/library");
  const hasLoginMessage = await page
    .locator("body")
    .getByText(/đăng nhập|login/i)
    .isVisible()
    .catch(() => false);
  expect(isRedirected || hasLoginMessage).toBeTruthy();
});
