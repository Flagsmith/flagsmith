import { getLogger, logResults } from '../helpers.cafe';
import segmentTest from '../tests/segment-test';

const logger = getLogger();

fixture`Segments Tests`
    .requestHooks(logger);

test('Segments Test', async () => {
    await segmentTest()
}).after(async (t) => {
    console.log('Start of Segment Requests');
    await logResults(logger.requests, t);
    console.log('End of Segment Requests');
});
