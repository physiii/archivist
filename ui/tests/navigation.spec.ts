import { expect, test } from "@playwright/test";

import {
  TEST_COLLECTION_NAME,
  TEST_MEDIA_ID,
  clickSidebarNav,
  mockAppApis,
  waitForRowsOrEmpty,
} from "./helpers/appMocks";

test.beforeEach(async ({ page }) => {
  await mockAppApis(page);
});

test("primary routes render their current shells", async ({ page }) => {
  await page.goto("/collections");
  await expect(page.getByRole("heading", { name: "Collections", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Collection catalog", exact: true })).toBeVisible();

  await clickSidebarNav(page, "Focus");
  await expect(page).toHaveURL(/\/focus$/);
  await expect(page.getByRole("heading", { name: "Focus", exact: true })).toBeVisible();
  await expect(page.getByRole("tablist", { name: "Focus lanes" })).toBeVisible();

  await clickSidebarNav(page, "Backup");
  await expect(page).toHaveURL(/\/backup$/);
  await expect(page.getByRole("heading", { name: "Backup", exact: true })).toBeVisible();

  await clickSidebarNav(page, "Indexing");
  await expect(page).toHaveURL(/\/indexing$/);
  await expect(page.getByRole("heading", { name: "Indexing", exact: true })).toBeVisible();

  await clickSidebarNav(page, "Media");
  await expect(page).toHaveURL(/\/media$/);
  await expect(page.getByRole("heading", { name: "Media Processing", exact: true })).toBeVisible();

  await clickSidebarNav(page, "Journal");
  await expect(page).toHaveURL(/\/journal$/);
  await expect(page.getByRole("heading", { name: "Journal", exact: true })).toBeVisible();
  await expect(page.locator(".journal-calendar-board")).toBeVisible();

  await clickSidebarNav(page, "Console");
  await expect(page).toHaveURL(/\/console$/);
  await expect(page.locator(".agent-console-page")).toBeVisible();
  await expect(page.getByRole("tab", { name: "Chat", exact: true })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Fleet", exact: true })).toBeVisible();
  await expect(page.getByRole("tab", { name: "System", exact: true })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Tests", exact: true })).toBeVisible();
});

test("collections and collection detail keep selection-driven inspectors", async ({ page }) => {
  await page.goto("/collections");

  const collectionRows = page.getByRole("list", { name: "Collection catalog" }).getByRole("button");
  const collectionState = await waitForRowsOrEmpty(page, collectionRows, page.getByText("No collections found"));
  if (collectionState === "rows") {
    await collectionRows.first().click();
    await expect(page.locator(".record-row.active").first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Collection details", exact: true })).toBeVisible();

    const openLinks = page.getByRole("link", { name: "Open collection" });
    if (await openLinks.count()) {
      await openLinks.last().click();
      await expect(page).toHaveURL(new RegExp(`/collections/${TEST_COLLECTION_NAME}$`));
      await expect(page.getByRole("heading", { name: "Collection schema", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Embeddings preview", exact: true })).toBeVisible();
    }
  } else {
    await expect(page.getByText("No collections found")).toBeVisible();
  }
});

test("operations pages expose row selection and inspectors", async ({ page }) => {
  await page.goto("/indexing");
  const indexingTargets = page.getByRole("list", { name: "Indexing targets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, indexingTargets, page.getByText("No targets configured"))) === "rows") {
    await indexingTargets.first().click();
    await expect(page.getByRole("heading", { name: "Target inspector", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No targets configured")).toBeVisible();
  }

  await page.goto("/backup");
  const backupTargets = page.getByRole("list", { name: "Backup targets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, backupTargets, page.getByText("No backup targets"))) === "rows") {
    await backupTargets.first().click();
    await expect(page.getByRole("heading", { name: "Target inspector", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No backup targets")).toBeVisible();
  }

  await page.goto("/media");
  const mediaAssets = page.getByRole("list", { name: "Processed media assets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, mediaAssets, page.getByText("No assets found"))) === "rows") {
    await mediaAssets.first().click();
    await expect(page).toHaveURL(new RegExp(`/media/${TEST_MEDIA_ID}$`));
    await expect(page.getByRole("heading", { name: "Source file", exact: true })).toBeVisible();
    await expect(page.getByRole("tablist", { name: "File detail views" })).toBeVisible();
    await page.getByRole("button", { name: "Back To Files" }).click();
    await expect(page).toHaveURL(/\/media$/);
    await expect(page.getByRole("heading", { name: "Processed files", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No assets found")).toBeVisible();
  }
});
