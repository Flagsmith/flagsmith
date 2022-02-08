// check-console-messages.js
import { t } from 'testcafe';

export default async function () {
    const { error, log } = await t.getBrowserConsoleMessages();
    console.log(`\n\n Test Errors: \n${error}\n\n`)
}
