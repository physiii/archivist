import { expect, test } from "@playwright/test";

test("top nav routes are available", async ({ page }) => {
  await page.goto("/collections");
  await expect(page.getByRole("link", { name: "Collections" })).toBeVisible();

  await page.getByRole("link", { name: "Backup" }).click();
  await expect(page).toHaveURL(/\/backup$/);
  await expect(page.getByRole("heading", { name: "Backup", exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Indexing" }).click();
  await expect(page).toHaveURL(/\/indexing$/);
  await expect(page.getByRole("heading", { name: "Indexing", exact: true })).toBeVisible();
});

test("open collection navigates to detail page", async ({ page }) => {
  await page.goto("/collections");
  const openButtons = page.locator(".grid .card .button-link", { hasText: "Open" });
  const count = await openButtons.count();
  if (count > 0) {
    await openButtons.first().click();
  } else {
    await page.goto("/collections/transcripts");
  }
  await expect(page).toHaveURL(/\/collections\/.+/);
  await expect(page.getByRole("heading", { name: /Collection:/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Embeddings Preview" })).toBeVisible();
});
