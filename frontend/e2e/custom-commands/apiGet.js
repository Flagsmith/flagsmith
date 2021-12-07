var util = require('util');
var events = require('events');

function apiGet() {}
util.inherits(apiGet, events.EventEmitter);

apiGet.prototype.command = function (apiUrl, success) {
    var request = require("request");

    request.get(apiUrl, function (error, response) {
        if (error) {
            console.log(error);
            return;
        }

        success(response);
        this.emit('complete');
    }.bind(this));
};

module.exports = apiGet;