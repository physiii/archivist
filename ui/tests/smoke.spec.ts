import { expect, test } from "@playwright/test";

test("collections page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Archivist")).toBeVisible();
  await expect(page.getByRole("link", { name: "Collections" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Backup" })).toBeVisible();

  // We expect at least one collection card to exist on a running Milvus-backed system.
  await expect(page.getByRole("link", { name: "Open" }).first()).toBeVisible({ timeout: 15_000 });
});

test("backup page renders key sections", async ({ page }) => {
  await page.goto("/backup");
  await expect(page.getByRole("heading", { name: "Backup Scheduler" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Backup Targets & Destinations" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Storage Health & Capacity" })).toBeVisible();
});

