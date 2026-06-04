import { expect, test, type Page } from "@playwright/test";

import { TEST_COLLECTION_NAME, TEST_MEDIA_ID, clickSidebarNav, mockAppApis } from "./helpers/appMocks";

type RouteContract = {
  label: string;
  path: string;
  assertReady: (page: Page) => Promise<void>;
};

const VIEWPORTS = [
  { name: "narrow-phone", width: 320, height: 568 },
  { name: "phone", width: 390, height: 844 },
  { name: "large-phone", width: 640, height: 960 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
  { name: "wide-desktop", width: 1720, height: 1117 },
];

const ROUTES: RouteContract[] = [
  {
    label: "Collections",
    path: "/collections",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Collections", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Collection catalog", exact: true })).toBeVisible();
    },
  },
  {
    label: "Collection Detail",
    path: `/collections/${TEST_COLLECTION_NAME}`,
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Collection schema", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Embeddings preview", exact: true })).toBeVisible();
    },
  },
  {
    label: "Focus",
    path: "/focus",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Focus", exact: true })).toBeVisible();
      await expect(page.getByRole("tablist", { name: "Focus lanes" })).toBeVisible();
      await expect(page.locator(".focus-lane-tab-panel")).toBeVisible();
    },
  },
  {
    label: "Backup",
    path: "/backup",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Backup", exact: true })).toBeVisible();
      await expect(page.getByRole("list", { name: "Backup targets" })).toBeVisible();
    },
  },
  {
    label: "Indexing",
    path: "/indexing",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Indexing", exact: true })).toBeVisible();
      await expect(page.getByRole("list", { name: "Indexing targets" })).toBeVisible();
    },
  },
  {
    label: "Media",
    path: "/media",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Media Processing", exact: true })).toBeVisible();
      await expect(page.getByRole("list", { name: "Processed media assets" })).toBeVisible();
    },
  },
  {
    label: "Media Detail",
    path: `/media/${TEST_MEDIA_ID}`,
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Source file", exact: true })).toBeVisible();
      await expect(page.getByRole("tablist", { name: "File detail views" })).toBeVisible();
    },
  },
  {
    label: "Journal",
    path: "/journal",
    assertReady: async (page) => {
      await expect(page.getByRole("heading", { name: "Journal", exact: true })).toBeVisible();
      await expect(page.locator(".journal-calendar-board")).toBeVisible();
      await expect(page.getByRole("slider", { name: "Journal timeline slider" })).toBeVisible();
    },
  },
  {
    label: "Console",
    path: "/console",
    assertReady: async (page) => {
      await expect(page.locator(".agent-console-page")).toBeVisible();
      await page.getByRole("tab", { name: "Fleet", exact: true }).click({ force: true });
      await expect(page.locator("[data-testid='fleet-agent-grid']")).toBeVisible();
      await page.getByRole("tab", { name: "System", exact: true }).click({ force: true });
      await expect(page.locator("[data-testid='system-regression-focus-priorities']")).toBeVisible();
      await page.getByRole("tab", { name: "Tests", exact: true }).click({ force: true });
      await expect(page.locator("[data-testid='tests-header']")).toBeVisible();
      await page.getByRole("tab", { name: "Chat", exact: true }).click({ force: true });
      await expect(page.locator("[data-testid='console-page']")).toBeVisible();
    },
  },
];

async function assertNoHorizontalOverflow(page: Page, label: string) {
  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    return {
      viewport: window.innerWidth,
      docClientWidth: doc.clientWidth,
      docScrollWidth: doc.scrollWidth,
      bodyScrollWidth: body.scrollWidth,
      mainScrollers: Array.from(document.querySelectorAll<HTMLElement>(".main-content, .main-content-shell, .workspace-page, .agent-console-page"))
        .map((node) => ({
          className: node.className,
          clientWidth: node.clientWidth,
          scrollWidth: node.scrollWidth,
        })),
    };
  });

  expect(metrics.docScrollWidth, `${label}: document overflowed horizontally`).toBeLessThanOrEqual(metrics.docClientWidth + 1);
  expect(metrics.bodyScrollWidth, `${label}: body overflowed horizontally`).toBeLessThanOrEqual(metrics.docClientWidth + 1);
  for (const scroller of metrics.mainScrollers) {
    expect(scroller.scrollWidth, `${label}: ${scroller.className} overflowed horizontally`).toBeLessThanOrEqual(scroller.clientWidth + 1);
  }
}

function filteredConsoleErrors(messages: string[]) {
  return messages.filter((message) => {
    if (message.includes("favicon")) return false;
    if (message.includes("Failed to load resource") && message.includes("favicon")) return false;
    return true;
  });
}

for (const viewport of VIEWPORTS) {
  test(`${viewport.name} route audit stays responsive and error-free`, async ({ page }) => {
    await mockAppApis(page);
    await page.setViewportSize({ width: viewport.width, height: viewport.height });

    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    for (const route of ROUTES) {
      await test.step(route.label, async () => {
        await page.goto(route.path);
        await route.assertReady(page);
        await page.waitForTimeout(100);
        await assertNoHorizontalOverflow(page, `${viewport.name} ${route.label}`);
      });
    }

    expect(pageErrors, `${viewport.name}: uncaught page errors`).toEqual([]);
    expect(filteredConsoleErrors(consoleErrors), `${viewport.name}: console errors`).toEqual([]);
  });
}

test("mobile drawer exposes the full primary route set", async ({ page }) => {
  await mockAppApis(page);
  await page.setViewportSize({ width: 390, height: 844 });

  await page.goto("/collections");
  await clickSidebarNav(page, "Focus");
  await expect(page).toHaveURL(/\/focus$/);

  await clickSidebarNav(page, "Backup");
  await expect(page).toHaveURL(/\/backup$/);

  await clickSidebarNav(page, "Indexing");
  await expect(page).toHaveURL(/\/indexing$/);

  await clickSidebarNav(page, "Media");
  await expect(page).toHaveURL(/\/media$/);

  await clickSidebarNav(page, "Journal");
  await expect(page).toHaveURL(/\/journal$/);

  await clickSidebarNav(page, "Console");
  await expect(page).toHaveURL(/\/console$/);
});
