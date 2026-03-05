import { defineConfig } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL?.trim() || "http://127.0.0.1:4173";
const useExternalServer = Boolean(process.env.PLAYWRIGHT_BASE_URL?.trim());

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  use: {
    baseURL,
    trace: "on-first-retry"
  },
  webServer: useExternalServer
    ? undefined
    : {
        command: "npm run build && npm run preview -- --host 127.0.0.1 --port 4173",
        port: 4173,
        reuseExistingServer: true
      }
});

