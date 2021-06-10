const SLACK_TOKEN = process.env.SLACK_TOKEN;
const Slackbots = require('slackbots');
const Project = require('../common/project');

if (!SLACK_TOKEN) {
    return;
}

const bot = new Slackbots({
    token: SLACK_TOKEN,
    name: `nightwatch-bot${Project.env === 'prod' ? '' : `-${Project.env}`}`,
});

const params = {
    icon_emoji: ':owl:',
    link_names: true,
};

const toChannel = function (message, channel) {
    console.log('Posting to channel', channel, 'Message is ', message);
    if (channel) {
        return bot.postMessageToChannel(channel, message, params, null);
    }
    return Promise.resolve();
};

module.exports = toChannel;
