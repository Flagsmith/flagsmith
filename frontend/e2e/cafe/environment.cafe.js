import { byId, click, getLogger, log, login, logResults, setText, waitForElementVisible } from '../helpers.cafe';
import environmentTest from '../tests/environment-test';

const logger = getLogger();

fixture`Environment Tests`
    .requestHooks(logger);


test('Submit a Form', async () => {
    await environmentTest()
}).after(async (t) => {
    console.log('Start of Environment Requests');
    await logResults(logger.requests, t);
    console.log('End of Environment Requests');
});
