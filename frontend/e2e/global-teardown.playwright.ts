import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { extractFailedTests } from './extract-failed-tests';
import { notifyFailure } from './helpers.playwright';

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown for E2E tests...');

  // Extract failed tests to a smaller JSON file for easier debugging
  extractFailedTests(__dirname);

  // Check for failures and notify via Slack
  const failedJsonPath = path.join(__dirname, 'test-results', 'failed.json');

  if (fs.existsSync(failedJsonPath) && !process.env.E2E_DEV) {
    try {
      const failedData = JSON.parse(fs.readFileSync(failedJsonPath, 'utf-8'));
      const failedCount = failedData.tests?.length || 0;

      if (failedCount > 0) {
        console.log(`Notifying Slack about ${failedCount} failed test(s)...`);
        await notifyFailure(failedCount);
        console.log('Slack notification sent');
      }
    } catch (e) {
      console.log('Error sending Slack notification:', e);
    }
  }

  console.log('E2E tests completed');
}

export default globalTeardown;
