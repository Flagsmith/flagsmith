var fs = require('fs');
var Slack = require('node-slack-upload');
var SLACK_TOKEN = process.env.SLACK_TOKEN;
var slack = new Slack(SLACK_TOKEN); //todo: move to env var if we host this in a public repo

module.exports = function (path, initialComment, channels, title) {
    return new Promise((resolve,reject)=>{
        slack.uploadFile({
            file: fs.createReadStream(path),
            filetype: 'auto',
            title,
            initialComment,
            channels,
        }, function(err, data) {
            if(err) {
                resolve({err})
            } else {
                resolve({data})
            }
        });
    })
}