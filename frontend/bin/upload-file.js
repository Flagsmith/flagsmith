require('dotenv').config();
const { WebClient } = require('@slack/web-api');
const fs = require('fs');

const SLACK_TOKEN = process.env.SLACK_TOKEN;

module.exports = function (path) {
    if (!SLACK_TOKEN) {
        console.log('Slack token not specified, skipping upload');
        return;
    }

    const parts = path.split('/');
    file = fs.createReadStream(path); // Optional, via multipart/form-data. If omitting this parameter, you MUST submit content
    filename = parts[parts.length - 1]; // Required
    title = 'Test Run'; // Optional
    channelId = 'C0102JZRG3G'; // infra_tests channel ID

    console.log(`Uploading ${path}`);
    const slackClient = new WebClient(process.env.SLACK_TOKEN);

    try {
        // Call the files.upload method using the WebClient
        const result = slackClient.files.upload({
            channels: channelId,
            initial_comment: title,
            file: fs.createReadStream(filename)
        });
        console.log(result);
    }
    catch (error) {
        console.error(error);
    }
};
