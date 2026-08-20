import { defineConfig } from '@playwright/test';

import { fileURLToPath } from 'node:url';

const backendPython = fileURLToPath(
  new URL('../backend/.venv/Scripts/python.exe', import.meta.url),
);

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: `"${backendPython}" -m uvicorn app.main:app --port 8000`,
      cwd: '../backend',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});