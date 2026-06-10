import * as fs from 'fs';
import * as path from 'path';

const SLACK_TOKEN = process.env.SLACK_TOKEN;
const CHANNEL_ID = 'C0102JZRG3G'; // infra_tests channel ID
const failedJsonPath = path.join(__dirname, 'test-results', 'failed.json');
const failedData = JSON.parse(fs.readFileSync(failedJsonPath, 'utf-8'));
const failedCount = failedData.failedTests?.length || 0;

async function slackPost(endpoint: string, body: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(`https://slack.com/api/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      Authorization: `Bearer ${SLACK_TOKEN}`,
    },
    body: JSON.stringify(body),
  });
  const data = await res.json() as { ok: boolean; error?: string };
  if (!data.ok) throw new Error(`Slack ${endpoint} error: ${data.error}`);
  return data;
}

async function uploadFile(filePath: string): Promise<void> {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping upload');
    return;
  }

  const epoch = Date.now();
  const filename = `playwright-report-${epoch}.zip`;
  const fileBytes = fs.readFileSync(filePath);
  const fileSize = fileBytes.byteLength;

  console.log(`Uploading ${filePath}`);
  const urlRes = await slackPost('files.getUploadURLExternal', {
    filename,
    length: fileSize,
  }) as { upload_url: string; file_id: string };


  const uploadRes = await fetch(urlRes.upload_url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: fileBytes,
  });
  if (!uploadRes.ok) {
    throw new Error(`Upload to pre-signed URL failed: ${uploadRes.status} ${uploadRes.statusText}`);
  }

  await slackPost('files.completeUploadExternal', {
    files: [{ id: urlRes.file_id, title: filename }],
    channel_id: CHANNEL_ID,
  });
}

function postMessage(message: string): Promise<unknown> {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping message');
    return Promise.resolve();
  }

  return slackPost('chat.postMessage', { channel: CHANNEL_ID, text: message });
}

function notifyFailure(failedCount: number, failedTests: any[]): Promise<unknown> {
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

  const prInfo = prNumber && prUrl
    ? `*PR:* <${prUrl}|#${prNumber}>${prTitle ? ` - ${prTitle}` : ''}\n`
    : '';

  const testNames = failedTests.slice(0, 3).map((t) => t.title).join(', ');
  const moreTests = failedCount > 3 ? ` +${failedCount - 3} more` : '';

  const message = `❌ E2E Tests Failed

${prInfo}*Branch:* ${branch}
*Test Type:* ${testType}
*Failed:* ${failedCount} test(s) - ${testNames}${moreTests}

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
    process.exit(0);
  });
