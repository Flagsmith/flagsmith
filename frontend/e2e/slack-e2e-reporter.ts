import * as fs from 'fs';
import * as path from 'path';
import { WebClient } from '@slack/web-api';

const SLACK_TOKEN = process.env.SLACK_TOKEN;
const CHANNEL_ID = 'C0102JZRG3G'; // infra_tests channel ID
const failedJsonPath = path.join(__dirname, 'test-results', 'failed.json');
const failedData = JSON.parse(fs.readFileSync(failedJsonPath, 'utf-8'));
const failedCount = failedData.failedTests?.length || 0;

async function uploadFile(filePath: string): Promise<void> {
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

function notifyFailure(
  failedCount: number,
  failedTests: any[],
): Promise<unknown> {
  const actionUrl = process.env.GITHUB_ACTION_URL || '';
  if (!actionUrl) {
    console.log('No GITHUB_ACTION_URL set, skipping Slack notification');
    return Promise.resolve();
  }

  const branch = process.env.GITHUB_REF_NAME || process.env.GITHUB_HEAD_REF || 'unknown';
  const testType = process.env.TEST_TYPE || 'unknown';
  const prNumber = process.env.PR_NUMBER;
  const prTitle = process.env.PR_TITLE;
  const prUrl = process.env.PR_URL;

  // Build PR info line
  const prInfo = prNumber && prUrl
    ? `*PR:* <${prUrl}|#${prNumber}>${prTitle ? ` - ${prTitle}` : ''}\n`
    : '';

  // Build failed tests list (limit to first 5 to avoid huge messages)
  const testList = failedTests
    .slice(0, 5)
    .map((test) => `• ${test.file}: ${test.title}`)
    .join('\n');
  const moreTests = failedCount > 5 ? `\n...and ${failedCount - 5} more` : '';

  const message = `❌ E2E Tests Failed

${prInfo}*Branch:* ${branch}
*Test Type:* ${testType}
*Failed:* ${failedCount} test(s)

*Failed Tests:*
${testList}${moreTests}

📦 View artifacts: ${actionUrl}`;

  return postMessage(message);
}

if (!fs.existsSync(failedJsonPath)) {
  console.log('No failed.json found, skipping Slack notification');
  process.exit(0);
}

if (failedCount === 0) {
  console.log('No failed tests, skipping Slack notification');
  process.exit(0);
}

async function main() {
  console.log(`Sending Slack notification for ${failedCount} failed test(s)...`);
  await notifyFailure(failedCount, failedData.failedTests || []);
  console.log('Slack notification sent successfully');

  // Upload HTML report if zip file exists
  const reportZipPath = path.join(__dirname, 'playwright-report.zip');
  if (fs.existsSync(reportZipPath)) {
    console.log('Uploading HTML report...');
    await uploadFile(reportZipPath);
    console.log('HTML report uploaded successfully');
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Failed to send Slack notification:', error);
    process.exit(1);
  });
