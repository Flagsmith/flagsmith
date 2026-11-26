import { describe, expect, it } from 'vitest';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { parseSimulatedDataset } from './dataset';

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
    seed: 42,
    generatedAt: '2026-11-26T12:00:00.000Z',
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
