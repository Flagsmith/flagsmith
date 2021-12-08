const createTestCafe = require('testcafe');
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');

const upload = require('../bin/upload-file');

let testcafe;
let server;

createTestCafe()
    .then(async (tc) => {
        testcafe = tc;
        await new Promise((resolve) => {
            process.env.PORT = 3000;
            server = fork('./server');
            server.on('message', () => {
                resolve();
            });
        });
        const runner = testcafe.createRunner();
        return runner
            .src(['./e2e/cafe'])
            .browsers(['chrome:headless'])
            .run();
    })
    .then(async (failedCount) => {
        // Clean up your database here...

        const dir = path.join(__dirname, '../reports/screen-captures');
        const files = fs.readdirSync(dir);
        await Promise.all(files.map(f => upload(path.join(dir, f))));
        server.kill('SIGINT');
        testcafe.close();
        process.exit(0);
    });
