const createTestCafe = require('testcafe');

let testcafe = null;
const { fork } = require('child_process');

createTestCafe()
    .then(async (tc) => {
        testcafe = tc;
        console.log('Runnnnnnn');

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
    .then((failedCount) => {
        // Clean up your database here...
        testcafe.close();
    });
