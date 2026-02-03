import * as fs from 'fs';
import * as path from 'path';
import { notifyFailure } from './helpers/e2e-helpers.playwright';

const failedJsonPath = path.join(__dirname, 'test-results', 'failed.json');

if (!fs.existsSync(failedJsonPath)) {
  console.log('No failed.json found, skipping Slack notification');
  process.exit(0);
}

const failedData = JSON.parse(fs.readFileSync(failedJsonPath, 'utf-8'));
const failedCount = failedData.failedTests?.length || 0;

if (failedCount === 0) {
  console.log('No failed tests, skipping Slack notification');
  process.exit(0);
}

console.log(`Sending Slack notification for ${failedCount} failed test(s)...`);
notifyFailure(failedCount)
  .then(() => {
    console.log('Slack notification sent successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Failed to send Slack notification:', error);
    process.exit(1);
  });
