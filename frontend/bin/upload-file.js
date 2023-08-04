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
  const channelId = 'C0102JZRG3G' // infra_tests channel ID

  // eslint-disable-next-line
    console.log(`Uploading ${path}`);

  const slackClient = new WebClient(process.env.SLACK_TOKEN)

  const { GITHUB_REF, GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_SERVER_URL } =
    process.env
  const githubInfo = GITHUB_SERVER_URL
    ? `${GITHUB_REF} ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}`
    : ''
  // Call the files.upload method using the WebClient
  return slackClient.files.upload({
    channels: channelId,
    file: fs.createReadStream(path),
    initial_comment: `${title} ${githubInfo}`,
  })
}
