import { FullConfig } from '@playwright/test';
import { extractFailedTests } from './extract-failed-tests';
import { notifyFailure } from './helpers/slack';

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown...');
  const failedCount = extractFailedTests(__dirname);

  if (failedCount > 0 && !process.env.E2E_DEV) {
    console.log(`Attempting Slack notification for ${failedCount} failed test(s)...`);
    console.log(`SLACK_TOKEN set: ${!!process.env.SLACK_TOKEN}`);
    try {
      await notifyFailure(failedCount);
      console.log('Slack notification sent');
    } catch (error) {
      console.error('Slack notification failed:', error);
    }
  }

  console.log('E2E tests completed');
}

export default globalTeardown;
