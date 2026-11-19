// The Python rehearsal driver provisions a dedicated local environment and passes
// its public SDK key on stdin. All writes use the same SDK calls as the drill.
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createFlagsmithInstance } from '@flagsmith/flagsmith/isomorphic';

const { action, environment, experiment, total, rates, winner } = JSON.parse(readFileSync(0, 'utf8'));
const client = createFlagsmithInstance();
const base = 'http://127.0.0.1:8000/api/';
const counts = { control: { exposed: 0, converted: 0 }, guided: { exposed: 0, converted: 0 } };
const identityPrefix = `first-minute-rehearsal-${experiment}-${action}${action === 'verify' ? '-' + randomUUID() : ''}`;

function simulatedConversion(identifier, rate) {
    const sample =
        createHash('sha256')
            .update('outcome/' + identifier)
            .digest()
            .readUInt32BE(0) /
        2 ** 32;
    return sample < rate;
}

try {
    await client.init({
        environmentID: environment,
        api: base + 'v1/',
        fetch: globalThis.fetch,
        enableEvents: action === 'sample',
        ...(action === 'sample' && { eventProcessorConfig: { eventsApiUrl: base } }),
    });
    for (let i = 0; i < total; i++) {
        const identity = `${identityPrefix}-${i}`;
        await client.identify(identity);
        if (action === 'verify') {
            const flag = client.getAllFlags().triage_guide;
            if (!flag?.enabled || flag.value !== winner || flag.experiment?.inExperiment) {
                throw new Error('The SDK did not serve the selected desk outside the experiment.');
            }
            continue;
        }
        if (action !== 'sample') throw new Error('Unknown rehearsal action.');
        const flag = client.getExperimentFlag('triage_guide');
        if (
            !flag?.enabled ||
            flag.experiment?.id !== experiment ||
            !flag.experiment.inExperiment ||
            !Object.hasOwn(counts, flag.value)
        ) {
            throw new Error('Expected an enrolled identity in the rehearsal experiment.');
        }
        counts[flag.value].exposed++;
        if (simulatedConversion(identity, rates[flag.value])) {
            client.trackEvent('drill_resolved');
            counts[flag.value].converted++;
        }
        if ((i + 1) % 20 === 0) await client.flushEvents();
    }
    await client.flushEvents();
} finally {
    await client.close(10000);
}

console.log(JSON.stringify(action === 'sample' ? counts : { verified: total }));
