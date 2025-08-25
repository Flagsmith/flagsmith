require('dotenv').config()
const { WebClient } = require('@slack/web-api')
const fs = require('fs')

const SLACK_TOKEN = process.env.SLACK_TOKEN

module.exports = function uploadFile(path) {
  if (!SLACK_TOKEN) {
    // eslint-disable-next-line
    console.log('Slack token not specified, skipping upload');
    return
  }

  const title = 'Test Run' // Optional
  const epoch = new Date().valueOf()
  const filename = `e2e-record-${epoch}.mp4`
  const channelId = 'C0102JZRG3G' // infra_tests channel ID
  // eslint-disable-next-line
  console.log(`Uploading ${path}`);

  const slackClient = new WebClient(SLACK_TOKEN)

  // Call the files.upload method using the WebClient
  return slackClient.files.uploadV2({
    channel_id: channelId,
    file: fs.createReadStream(path),
    filename,
    initial_comment: `✖ ${title} ${process.env.GITHUB_ACTION_URL || ''}`,
  })
}
new Date().valueOf()
