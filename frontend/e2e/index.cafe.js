const createTestCafe = require('testcafe');
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');
const _options = require("../.testcaferc.js")
const upload = require('../bin/upload-file');
const minimist = require('minimist');
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
// Parse CLI arg --meta-filter
const args = minimist(process.argv.slice(2));
const filterString = args['meta-filter']; // "type=smoke,priority=high"
const metaConditions = (filterString || '')
    .split(',')
    .map(pair => {
        const [key, value] = pair.split('=');
        return { key, value };
    });
createTestCafe()
    .then(async (tc) => {
        testcafe = tc;
        await new Promise((resolve) => {
            if (process.env.E2E_LOCAL) {
                server = fork('./api/index');
                server.on('message', () => {
                    resolve();
                });
            } else {
                process.env.PORT = 3000;
                resolve()
            }
        });
        const runner = testcafe.createRunner()
        const args = process.argv.splice(2).map(value => value.toLowerCase());
        console.log('Filter tests:', args)
        const concurrentInstances = process.env.E2E_CONCURRENCY ?? 3
        console.log('E2E Concurrency:', concurrentInstances)

        return runner
            .clientScripts('e2e/add-error-logs.js')
            .src(['./e2e/init.cafe.js'])
            .concurrency(parseInt(concurrentInstances))
            .filter((_testName, _fixtureName, _fixturePath, testMeta, fixtureMeta) => {
                return metaConditions.some(({ key, value }) => {
                    return (
                        testMeta[key] === value || fixtureMeta[key] === value
                    );
                });
            })
            .run(options)
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
