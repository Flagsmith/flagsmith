const createTestCafe = require('testcafe');
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');
const _options = require("../.testcaferc")
const upload = require('../bin/upload-file');
const options = {
    ..._options,
    browsers: process.env.E2E_DEV ? ['firefox'] : ['firefox:headless'],
    debugOnFail: !!process.env.E2E_DEV
}
let testcafe;
let server;
const dir = path.join(__dirname, '../reports/screen-captures');
if (fs.existsSync(dir)) {
    fs.rmdirSync(dir, { recursive: true });
}
const start = Date.now().valueOf();
createTestCafe()
    .then(async (tc) => {
        testcafe = tc;
        await new Promise((resolve) => {
            process.env.PORT = 3000;
            server = fork('./api/index');
            server.on('message', () => {
                resolve();
            });
        });
        const runner = testcafe.createRunner()
        return runner
            .clientScripts('e2e/add-error-logs.js')
            .src(['./e2e/init.cafe.js'])
            .run(options)
            .then((v) => {
                if (!v) {
                    return runner
                        .clientScripts('e2e/add-error-logs.js')
                        .src(['./e2e/cafe'])
                        .concurrency(2)
                        .run(options);
                }
                return v;
            });
    })
    .then(async (v) => {
        // Upload files
        console.log(`Test failures ${v} in ${Date.now().valueOf() - start}ms`);
        if (fs.existsSync(dir) && !process.env.E2E_DEV) {
            try {
                const files = fs.readdirSync(dir);
                await Promise.all(files.map(f => upload(path.join(dir, f))));
            } catch (e) { console.log('error uploading files', e); }
        } else {
            console.log('No files to upload');
        }
        // Shut down server and testcafe
        server.kill('SIGINT');
        testcafe.close();
        process.exit(v);
    });
