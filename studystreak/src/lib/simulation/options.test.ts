import { describe, expect, it } from 'vitest';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { DEFAULT_OPTIONS, parseSimulationOptions } from './options';

describe('parseSimulationOptions', () => {
    it('uses the defaults with no arguments', () => {
        expect(parseSimulationOptions([])).toEqual(DEFAULT_OPTIONS);
        expect(DEFAULT_OPTIONS).toMatchObject({ visitors: 1000, signupRate: { control: 0.1, social_proof: 0.12 } });
    });

    it('applies every option without mutating the defaults', () => {
        const options = parseSimulationOptions([
            '--visitors',
            '200',
            '--seed',
            '9',
            '--control-signup-rate',
            '0.2',
            '--social-proof-signup-rate',
            '0.25',
            '--click-to-signup-rate',
            '0.5',
            '--median-click-seconds',
            '12',
        ]);
        expect(options).toEqual({
            visitors: 200,
            seed: 9,
            signupRate: { control: 0.2, social_proof: 0.25 },
            clickToSignupRate: 0.5,
            medianClickSeconds: 12,
        });
        expect(DEFAULT_OPTIONS.signupRate.control).toBe(0.1);
    });

    it.each([
        [['--visitors', '0']],
        [['--visitors', '10001']],
        [['--visitors', '10.5']],
        [['--visitors']],
        [['--visitors', '']],
        [['--visitors', 'many']],
        [['--seed', '-1']],
        [['--seed', '4294967296']],
        [['--control-signup-rate', '1.2']],
        [['--social-proof-signup-rate', '-0.1']],
        [['--click-to-signup-rate', '0']],
        [['--social-proof-signup-rate', '0.7']],
        [['--median-click-seconds', '0']],
        [['--verbose', '1']],
    ])('rejects %j', (args) => {
        expect(() => parseSimulationOptions(args)).toThrow(InvalidDataError);
    });
});
