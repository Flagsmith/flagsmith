import * as fs from 'fs';
import * as path from 'path';
import { WebClient } from '@slack/web-api';

const SLACK_TOKEN = process.env.SLACK_TOKEN;
const CHANNEL_ID = 'C0102JZRG3G'; // infra_tests channel ID

function postMessage(message: string): Promise<unknown> {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping message');
    return Promise.resolve();
  }

  const slackClient = new WebClient(SLACK_TOKEN);
  return slackClient.chat.postMessage({
    channel: CHANNEL_ID,
    text: message,
  });
}

function notifyFailure(failedCount: number): Promise<unknown> {
  const actionUrl = process.env.GITHUB_ACTION_URL || '';
  if (!actionUrl) {
    console.log('No GITHUB_ACTION_URL set, skipping Slack notification');
    return Promise.resolve();
  }

  const message = `❌ E2E Tests Failed: ${failedCount} test(s) failed\n\n📦 View artifacts: ${actionUrl}`;
  return postMessage(message);
}

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
