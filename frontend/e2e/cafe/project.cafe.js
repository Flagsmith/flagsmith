import { byId, click, getLogger, log, login, logResults, setText, waitForElementVisible } from '../helpers.cafe';
import projectTest from '../tests/project-test';

const logger = getLogger();

fixture`Project Tests`
    .page`http://localhost:3000/`
    .requestHooks(logger);

test('Project Test', async () => {
    await projectTest()
}).after(async (t) => {
    console.log('Start of Project Requests');
    await logResults(logger.requests,t );
    console.log('End of Project Requests');
});
