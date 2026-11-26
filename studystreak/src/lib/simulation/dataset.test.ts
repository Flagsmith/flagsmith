import { describe, expect, it } from 'vitest';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { simulatedRun } from '@/test/simulated-dataset';
import { parseSimulatedDataset, SIMULATED_DISCLOSURE } from './dataset';

const visitor = (overrides: Record<string, unknown> = {}) => ({
    visitorId: 'sim-0001',
    variant: 'control',
    clickedAfterSeconds: 3.4,
    signedUp: true,
    ...overrides,
});

const dataset = (overrides: Record<string, unknown> = {}) => ({
    kind: 'simulated',
    environment: 'simulation',
    disclosure: SIMULATED_DISCLOSURE,
    seed: 42,
    generatedAt: '2026-11-26T12:00:00.000Z',
    run: simulatedRun(Array.isArray(overrides.visitors) ? overrides.visitors.length : 1),
    visitors: [visitor()],
    ...overrides,
});

describe('parseSimulatedDataset', () => {
    it('accepts a valid simulated dataset unchanged', () => {
        expect(parseSimulatedDataset(dataset())).toEqual(dataset());
    });

    it('accepts an empty dataset', () => {
        expect(parseSimulatedDataset(dataset({ visitors: [] })).visitors).toEqual([]);
    });

    it.each([
        ['real data', { kind: 'real' }],
        ['the Production environment', { environment: 'production' }],
        ['a missing seed', { seed: undefined }],
        ['an invalid timestamp', { generatedAt: 'yesterday' }],
        ['a non-array visitors field', { visitors: {} }],
        ['a missing disclosure', { disclosure: '' }],
        ['a missing run', { run: undefined }],
        ['a run whose counts do not add up', { run: simulatedRun(5) }],
        [
            'a run with more confirmed than tracked events',
            {
                run: simulatedRun(1, {
                    eventDelivery: {
                        $flag_exposure: { tracked: 1, confirmed: 2 },
                        signup_clicked: { tracked: 0, confirmed: 0 },
                        signed_up: { tracked: 0, confirmed: 0 },
                    },
                }),
            },
        ],
        [
            'a run with an impossible signup rate',
            { run: simulatedRun(1, { signupRate: { control: 1.5, social_proof: 0.1 } }) },
        ],
        ['a run with an unnamed environment', { run: { ...simulatedRun(1), environmentName: 7 } }],
    ])('rejects %s', (_case, overrides) => {
        expect(() => parseSimulatedDataset(dataset(overrides))).toThrow(InvalidDataError);
    });

    it.each([
        ['an identity without the sim- prefix', { visitorId: '6f1c3c1e-5b7a-4d2e-9f8a-3c2b1a0d9e8f' }],
        ['an unknown variant', { variant: 'treatment' }],
        ['a negative click time', { clickedAfterSeconds: -0.5 }],
        ['a non-numeric click time', { clickedAfterSeconds: '3' }],
        ['a non-boolean signup', { signedUp: 'yes' }],
        ['a signup without a click', { clickedAfterSeconds: null, signedUp: true }],
    ])('rejects %s', (_case, overrides) => {
        expect(() => parseSimulatedDataset(dataset({ visitors: [visitor(overrides)] }))).toThrow(/visitors\[0\]/);
    });

    it('rejects duplicate visitors', () => {
        expect(() => parseSimulatedDataset(dataset({ visitors: [visitor(), visitor()] }))).toThrow('unique');
    });

    it.each([null, [], 'data'])('rejects a non-object document (%j)', (raw) => {
        expect(() => parseSimulatedDataset(raw)).toThrow(InvalidDataError);
    });
});
