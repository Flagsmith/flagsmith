import { getLogger, logResults } from '../helpers.cafe';
import inviteTest from '../tests/invite-test';

const logger = getLogger()

fixture`Invite Tests`.page`http://localhost:3000/`.requestHooks(logger)

test('Invite Test', async () => {
 await inviteTest()
}).after(async (t) => {
    console.log('Start of Invite Requests');
    await logResults(logger.requests, t);
    console.log('End of Invite Requests');
});
