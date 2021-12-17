const createTestCafe = require('testcafe');
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');

const upload = require('../bin/upload-file');

let testcafe;
let server;
const dir = path.join(__dirname, '../reports/screen-captures');
if (fs.existsSync(dir)) {
    fs.rmdirSync(dir, { recursive: true });
}
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
            .src(['./e2e/init.cafe.js'])
            .browsers(process.env.E2E_DEV ? ['chrome:headless'] : ['chrome:headless']) // always headless
            .run()
            .then((v) => {
                if (!v) {
                    return runner
                        .src(['./e2e/cafe'])
                        .browsers(process.env.E2E_DEV ? ['chrome'] : ['chrome:headless'])
                        .concurrency(4)
                        .run();
                }
                return v;
            });
    })
    .then(async (v) => {
        // Upload files
        console.log(`Test failures ${v}`);
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
