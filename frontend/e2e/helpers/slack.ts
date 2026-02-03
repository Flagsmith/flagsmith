import { WebClient } from '@slack/web-api';
import * as fs from 'fs';
import * as path from 'path';

const SLACK_TOKEN = process.env.SLACK_TOKEN;
const CHANNEL_ID = 'C0102JZRG3G'; // infra_tests channel

export async function uploadFile(filePath: string): Promise<void> {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping upload');
    return;
  }

  const epoch = Date.now();
  const ext = path.extname(filePath);
  const basename = path.basename(filePath);

  const isPlaywrightReport = basename === 'playwright-report.zip';
  const filename = isPlaywrightReport
    ? `playwright-report-${epoch}.zip`
    : `e2e-artifact-${epoch}${ext}`;
  const comment = isPlaywrightReport
    ? `📊 Playwright HTML Report ${process.env.GITHUB_ACTION_URL || ''}`
    : `✖ Test Run ${process.env.GITHUB_ACTION_URL || ''}`;

  console.log(`Uploading ${filePath}`);

  const slackClient = new WebClient(SLACK_TOKEN);
  await slackClient.files.uploadV2({
    channel_id: CHANNEL_ID,
    file: fs.createReadStream(filePath),
    filename,
    initial_comment: comment,
  });
}

export async function notifyFailure(failedCount: number): Promise<void> {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping notification');
    return;
  }

  const slackClient = new WebClient(SLACK_TOKEN);
  await slackClient.chat.postMessage({
    channel: CHANNEL_ID,
    text: `❌ E2E Tests Failed: ${failedCount} test(s) failed ${process.env.GITHUB_ACTION_URL || ''}`,
  });
}
