import os from "node:os";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const apiPort = process.env.CONTRATAMYPE_API_PORT ?? "8010";
const webPort = process.env.CONTRATAMYPE_WEB_PORT ?? "3100";
const testDb =
  process.env.CONTRATAMYPE_TEST_DB ??
  path.join(os.tmpdir(), "contratamype-e2e", "contratamype-test.duckdb");
const python =
  process.platform === "win32"
    ? path.join("..", ".venv", "Scripts", "python.exe")
    : path.join("..", ".venv", "bin", "python");

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" tests/serve_api.py`,
      url: `http://127.0.0.1:${apiPort}/health`,
      timeout: 120_000,
      reuseExistingServer: false,
      env: {
        CONTRATAMYPE_API_PORT: apiPort,
        CONTRATAMYPE_DB: testDb,
      },
    },
    {
      command: `npm run dev -- --port ${webPort}`,
      url: `http://127.0.0.1:${webPort}`,
      timeout: 180_000,
      reuseExistingServer: false,
      env: {
        CONTRATAMYPE_API_URL: `http://127.0.0.1:${apiPort}`,
      },
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
