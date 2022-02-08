// check-console-messages.js
import { t } from 'testcafe';

export default async function () {
    t.addRequestHooks()
    const { error, log } = await t.getBrowserConsoleMessages();
    console.log(`\n\n Test Logs: \n${log}\n\n`)
}
