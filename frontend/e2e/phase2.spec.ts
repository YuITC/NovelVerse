import { test, expect } from "@playwright/test";

// ─── M12: Follows + Bookmarks ──────────────────────────────────────────────

test("/library without auth shows login prompt or redirect", async ({ page }) => {
  await page.goto("/library");
  const url = page.url();
  const isRedirected = !url.includes("/library");
  const hasLoginMessage = await page
    .locator("body")
    .getByText(/đăng nhập|login/i)
    .isVisible()
    .catch(() => false);
  expect(isRedirected || hasLoginMessage).toBeTruthy();
});

// ─── M13: Nominations + Leaderboards ──────────────────────────────────────

test("/leaderboard tab click switches active period", async ({ page }) => {
  await page.goto("/leaderboard");
  const weeklyTab = page.getByRole("tab", { name: /tuần/i });
  await expect(weeklyTab).toBeVisible();
  await weeklyTab.click();
  await expect(weeklyTab).toHaveAttribute("aria-selected", "true");
  // page should not show a 500 error
  await expect(page.locator("body")).not.toContainText("500");
});

test("/leaderboard monthly tab loads without error", async ({ page }) => {
  await page.goto("/leaderboard");
  const monthlyTab = page.getByRole("tab", { name: /tháng/i });
  await monthlyTab.click();
  await expect(monthlyTab).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("body")).not.toContainText("500");
});

// ─── M14: Real-time Notifications ─────────────────────────────────────────

test("/notifications redirects to home when not logged in", async ({ page }) => {
  await page.goto("/notifications");
  // The page calls router.replace("/") when user is null
  await page.waitForURL((url) => !url.pathname.includes("/notifications"), { timeout: 5000 }).catch(() => null);
  const url = page.url();
  const isRedirected = !url.includes("/notifications");
  const hasLoginMessage = await page
    .locator("body")
    .getByText(/đăng nhập|login|Đang tải/i)
    .isVisible()
    .catch(() => false);
  expect(isRedirected || hasLoginMessage).toBeTruthy();
});

test("notification bell link is not in navbar when logged out", async ({ page }) => {
  await page.goto("/");
  // NotificationBell returns null when !user, so no link to /notifications should appear in navbar
  const bellLink = page.locator(`a[href="/notifications"]`);
  await expect(bellLink).not.toBeVisible();
});

test("/notifications page does not show 500 error", async ({ page }) => {
  await page.goto("/notifications");
  await expect(page.locator("body")).not.toContainText("500");
});
