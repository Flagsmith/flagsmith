import { test as teardown } from '@playwright/test';

teardown('kill bundled app', async ({ }) => {

  if (process.env.E2E_LOCAL) {
    console.log('E2E_LOCAL is set, skipping server stop')
    return
  }

  const pid = process.env.PLAYWRIGHT_BUNDLED_SERVER_PID;
  if (pid) {
    try {
      process.kill(Number(pid));
      console.log('Server stopped.');
    } catch (err) {
      console.warn('Failed to stop server:', err);
    }
  } else {
    console.log('No bundled app to stop');
  }
  console.log('teardown complete');
});