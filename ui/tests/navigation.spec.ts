import { expect, test, type Page } from "@playwright/test";

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

async function setFormValue(page: Page, placeholder: string, value: string) {
  const escapedPlaceholder = placeholder.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const field = page.locator(`input[placeholder="${escapedPlaceholder}"], textarea[placeholder="${escapedPlaceholder}"]`).first();
  await field.waitFor({ state: "attached" });
  const box = await field.boundingBox();
  if (!box) throw new Error(`Missing visible form field with placeholder "${placeholder}".`);
  await page.mouse.click(box.x + Math.min(12, box.width / 2), box.y + Math.min(12, box.height / 2));
  await page.keyboard.press("Control+A");
  await page.keyboard.type(value);
}

async function mockCollectionDetailOnlyApis(page: Page) {
  await page.unroute("**/api/**");
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const { pathname } = url;
    let payload: unknown = {};

    if (pathname === "/api/integrations/status") {
      payload = { integrations: [] };
    } else if (pathname === "/api/chat/sessions") {
      payload = { sessions: [], oc_sessions: [] };
    } else if (pathname === `/api/collections/${TEST_COLLECTION_NAME}`) {
      payload = {
        name: TEST_COLLECTION_NAME,
        raw_name: TEST_COLLECTION_NAME,
        num_entities: 42,
        fields: [
          { name: "id", dtype: "int64", is_primary: true, auto_id: false },
          { name: "text", dtype: "varchar" },
        ],
      };
    } else if (pathname === `/api/collections/${TEST_COLLECTION_NAME}/search`) {
      payload = {
        results: [
          {
            id: "row-1",
            distance: 0.12,
            text: "Transcript result",
            path: "/data/transcripts/demo.txt",
            creation_date: "2026-04-06",
          },
        ],
      };
    } else if (pathname === `/api/collections/${TEST_COLLECTION_NAME}/embeddings-preview`) {
      payload = {
        collection: TEST_COLLECTION_NAME,
        raw_name: TEST_COLLECTION_NAME,
        vector_dim: 1024,
        points: [
          { id: "row-1", vector: [0.1, 0.2, 0.3], text: "Transcript result", label: "row-1" },
        ],
        meta: { projection_method: "pca", axis_labels: ["X", "Y", "Z"] },
      };
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(payload),
    });
  });
}

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

test("collections search results expand inline", async ({ page }) => {
  await page.goto("/collections");

  const catalogRows = page.getByRole("list", { name: "Collection catalog" }).locator(".collection-catalog-row");
  await expect(catalogRows.first()).toContainText(TEST_COLLECTION_NAME);
  await catalogRows.first().locator(".collection-row-trigger").click({ force: true });
  await expect(catalogRows.first().locator(".collection-row-expanded")).toContainText("Rows");
  await expect(catalogRows.first().locator(".collection-row-expanded")).toContainText("Open collection");
  await expect(page.getByRole("heading", { name: "Collection details", exact: true })).toHaveCount(0);

  await setFormValue(page, "Search across all collections", "transcript");
  await page.getByRole("button", { name: "Search", exact: true }).click({ force: true });
  const globalResults = page.getByRole("list", { name: "Global search results" }).locator(".record-row");
  await expect(globalResults.first()).toContainText("Transcript match");
  await globalResults.first().locator(".record-row-click").click({ force: true });
  await expect(globalResults.first().locator(".record-row-expanded")).toContainText("Row id");
  await expect(globalResults.first().locator(".record-row-expanded")).toContainText("Transcript match");
  await expect(page.getByRole("heading", { name: "Result inspector", exact: true })).toHaveCount(0);
});

test("collection detail search results expand inline", async ({ page }) => {
  await mockCollectionDetailOnlyApis(page);
  await page.setViewportSize({ width: 1440, height: 1600 });
  await page.goto(`/collections/${TEST_COLLECTION_NAME}?q=transcript`);
  await expect(page).toHaveURL(new RegExp(`/collections/${TEST_COLLECTION_NAME}\\?q=transcript$`));
  await expect(page.getByRole("heading", { name: "Collection schema", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Embeddings preview", exact: true })).toBeVisible();

  const detailResults = page.getByRole("list", { name: "Collection search results" }).locator(".record-row");
  await expect(detailResults.first()).toContainText("Transcript result");
  await expect(detailResults.first().locator(".record-row-expanded")).toContainText("Row id");
  await expect(detailResults.first().locator(".record-row-expanded")).toContainText("Transcript result");
  await expect(page.getByRole("heading", { name: "Result inspector", exact: true })).toHaveCount(0);
});

test("operations pages expose row selection and inspectors", async ({ page }) => {
  await page.goto("/indexing");
  const indexingTargets = page.getByRole("list", { name: "Indexing targets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, indexingTargets, page.getByText("No targets configured"))) === "rows") {
    await indexingTargets.first().click({ force: true });
    await expect(page.getByRole("heading", { name: "Target inspector", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No targets configured")).toBeVisible();
  }

  await page.goto("/backup");
  const backupTargets = page.getByRole("list", { name: "Backup targets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, backupTargets, page.getByText("No backup targets"))) === "rows") {
    await backupTargets.first().click({ force: true });
    await expect(page.getByRole("heading", { name: "Target inspector", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No backup targets")).toBeVisible();
  }

  await page.goto("/media");
  const mediaAssets = page.getByRole("list", { name: "Processed media assets" }).getByRole("button");
  if ((await waitForRowsOrEmpty(page, mediaAssets, page.getByText("No assets found"))) === "rows") {
    await mediaAssets.first().click({ force: true });
    await expect(page).toHaveURL(new RegExp(`/media/${TEST_MEDIA_ID}$`));
    await expect(page.getByRole("heading", { name: "Source file", exact: true })).toBeVisible();
    await expect(page.getByRole("tablist", { name: "File detail views" })).toBeVisible();
    await page.getByRole("button", { name: "Back To Files" }).click({ force: true });
    await expect(page).toHaveURL(/\/media$/);
    await expect(page.getByRole("heading", { name: "Processed files", exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("No assets found")).toBeVisible();
  }
});
