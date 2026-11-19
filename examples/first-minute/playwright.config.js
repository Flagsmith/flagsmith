import { defineConfig } from '@playwright/test';

const baseURL = 'http://127.0.0.1:4185';

export default defineConfig({
    testDir: './tests',
    use: {
        baseURL,
        launchOptions: { executablePath: process.env.CHROMIUM_EXECUTABLE },
    },
    webServer: {
        command: 'npm run build:practice && npm run dev -- --host 127.0.0.1 --port 4185 --strictPort',
        url: baseURL,
        env: {
            VITE_FLAGSMITH_ENVIRONMENT_ID: 'browser-test',
            VITE_FLAGSMITH_ORIGIN: '',
            VITE_FLAGSMITH_DASHBOARD_URL: '',
        },
    },
});
