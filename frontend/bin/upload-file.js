require('dotenv').config()
const { WebClient } = require('@slack/web-api')
const fs = require('fs')
const path = require('path')

const SLACK_TOKEN = process.env.SLACK_TOKEN

function uploadFile(filePath) {
  if (!SLACK_TOKEN) {
    // eslint-disable-next-line
    console.log('Slack token not specified, skipping upload');
    return
  }

  const title = 'Test Run'
  const epoch = new Date().valueOf()
  const ext = path.extname(filePath)
  const basename = path.basename(filePath)

  // Determine filename and comment based on file type
  let filename
  let comment
  if (basename === 'playwright-report.zip') {
    filename = `playwright-report-${epoch}.zip`
    comment = `📊 Playwright HTML Report ${process.env.GITHUB_ACTION_URL || ''}`
  } else {
    filename = `e2e-artifact-${epoch}${ext}`
    comment = `✖ ${title} ${process.env.GITHUB_ACTION_URL || ''}`
  }

  const channelId = 'C0102JZRG3G' // infra_tests channel ID
  // eslint-disable-next-line
  console.log(`Uploading ${filePath}`);

  const slackClient = new WebClient(SLACK_TOKEN)

  // Call the files.upload method using the WebClient
  return slackClient.files.uploadV2({
    channel_id: channelId,
    file: fs.createReadStream(filePath),
    filename,
    initial_comment: comment,
  })
}

async function notifyFailure(failedCount) {
  if (!SLACK_TOKEN) {
    console.log('Slack token not specified, skipping notification')
    return
  }

  const channelId = 'C0102JZRG3G' // infra_tests channel ID
  const slackClient = new WebClient(SLACK_TOKEN)

  await slackClient.chat.postMessage({
    channel: channelId,
    text: `❌ E2E Tests Failed: ${failedCount} test(s) failed ${
      process.env.GITHUB_ACTION_URL || ''
    }`,
  })
}

module.exports = { notifyFailure, uploadFile }
