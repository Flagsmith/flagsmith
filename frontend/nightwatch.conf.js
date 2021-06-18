const chromedriver = require('chromedriver');

const SCREENSHOT_PATH = './screenshots/';
const os = require('os');

const browserSize = 'window-size=1920,1536';

// we use a nightwatch.conf.js file so we can include comments and helper functions
module.exports = {
    'src_folders': [
        'tests', // Where you are storing your Nightwatch e2e tests
    ],
    'output_folder': './reports', // reports (test outcome) output by nightwatch
    'custom_commands_path': ['./tests/custom-commands'],
    /*'selenium': {
        'start_process': true, // tells nightwatch to start/stop the selenium process
        'server_path': seleniumServer.path,
        'host': '127.0.0.1',
        'port': 4444, // standard selenium port
        'cli_args': {
            'webdriver.chrome.driver': chromedriver.path,
        },
    },
    */
    "webdriver": {
        "start_process": true,
        "server_path": "node_modules/.bin/chromedriver",
        "port": 4444
    },
    'test_settings': {
        'default': {
            'end_session_on_fail': false,
            'screenshots': {
                'enabled': false, // if you want to keep screenshots
                'path': './e2e_screenshots', // save screenshots here
                'on_failure': true,
                'on_error': true,
            },
            'globals': {
                'waitForConditionTimeout': 10000, // sometimes internet is slow so wait.
                'asyncHookTimeout': 200000000,
            },
            'desiredCapabilities': { // use Chrome as the default browser for tests
                'browserName': 'chrome',
                'javascriptEnabled': true, // turn off to test progressive enhancement
                'goog:chromeOptions': {
                    "args" : [
                        "headless",
                        "window-size=1920,1080"
                    ],
                    w3c: false,
                },
            },
        },
    },
};

function padLeft(count) { // theregister.co.uk/2016/03/23/npm_left_pad_chaos/
    return count < 10 ? `0${count}` : count.toString();
}

let FILECOUNT = 0; // "global" screenshot file count
/**
 * The default is to save screenshots to the root of your project even though
 * there is a screenshots path in the config object above! ... so we need a
 * function that returns the correct path for storing our screenshots.
 * While we're at it, we are adding some meta-data to the filename, specifically
 * the Platform/Browser where the test was run and the test (file) name.
 */
function imgpath(browser) {
    const a = browser.options.desiredCapabilities;
    const meta = [a.platform];
    meta.push(a.browserName ? a.browserName : 'any');
    meta.push(a.version ? a.version : 'any');
    meta.push(a.name); // this is the test filename so always exists.
    const metadata = meta.join('~').toLowerCase().replace(/ /g, '');
    return `${SCREENSHOT_PATH + metadata}_${padLeft(FILECOUNT++)}_`;
}

module.exports.imgpath = imgpath;
module.exports.SCREENSHOT_PATH = SCREENSHOT_PATH;