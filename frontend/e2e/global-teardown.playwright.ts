import { FullConfig } from '@playwright/test';
import { extractFailedTests } from './extract-failed-tests';
import { notifyFailure } from './helpers/slack';

async function globalTeardown(config: FullConfig) {
  const failedCount = extractFailedTests(__dirname);

  if (failedCount > 0 && !process.env.E2E_DEV) {
    await notifyFailure(failedCount);
  }

  console.log('E2E tests completed');
}

export default globalTeardown;
