import { exec, spawn } from 'child_process';

import { test as setup } from '@playwright/test';

require('dotenv').config()


setup('serve bundled app', async ({ }) => {
  if (process.env.E2E_LOCAL) {
    console.log('E2E_LOCAL is set, skipping server start')
    return
  }

  const port = process.env.PORT || '8080';
  const serverProcess = spawn('node', ['api/index.js'], {
    shell: true,
    stdio: 'inherit',
    env: {
      ...process.env,
      PORT: port,
    },
  });
  process.env.PLAYWRIGHT_BUNDLED_SERVER_PID = String(serverProcess.pid);
  // Wait for server to start
  await new Promise((resolve) => setTimeout(resolve, 3000));
  console.log(`Serving bundled app on port ${port}`)
});