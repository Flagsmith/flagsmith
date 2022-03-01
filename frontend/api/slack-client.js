const { WebClient } = require('@slack/web-api');

if (!process.env.SLACK_TOKEN) {
    return;
}

const web = new WebClient(process.env.SLACK_TOKEN);

const toChannel = async function (message, channel) {
    console.log("sending to channel: " + channel + " message: " + message);
    try {
        await web.chat.postMessage({
            channel: '#' + channel,
            text: message,
        });
    } catch (error) {
        console.log("Error posting to Slack:" + error);
    }
};

module.exports = toChannel;
