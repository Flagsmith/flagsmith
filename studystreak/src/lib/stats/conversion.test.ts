import { describe, expect, it } from 'vitest';
import { compareConversion } from './conversion';
import { InvalidDataError } from './invalid-data-error';

// References: SciPy 1.18.1 and mpmath for exact values; 4 million NumPy draws for the interval estimates.
describe('compareConversion', () => {
    const result = compareConversion({ visitors: 500, conversions: 50 }, { visitors: 500, conversions: 62 });

    it('reports observed rates, absolute difference and relative lift', () => {
        expect(result.control.observedRate).toBe(0.1);
        expect(result.treatment.observedRate).toBe(0.124);
        expect(result.observedAbsoluteDifference).toBeCloseTo(0.024, 12);
        expect(result.observedRelativeLift).toBeCloseTo(0.24, 12);
    });

    it('uses a Beta(1, 1) prior for the posteriors and their 95% credible intervals', () => {
        expect(result.control.posteriorMean).toBeCloseTo(51 / 502, 12);
        expect(result.control.credibleInterval.lower).toBeCloseTo(0.07673686025971445, 9);
        expect(result.control.credibleInterval.upper).toBeCloseTo(0.12945448809721105, 9);
        expect(result.treatment.credibleInterval.lower).toBeCloseTo(0.09799725535381988, 9);
        expect(result.treatment.credibleInterval.upper).toBeCloseTo(0.1558233703656067, 9);
    });

    it('computes the exact probability that treatment beats control', () => {
        expect(result.probabilityTreatmentBeatsControl).toBeCloseTo(0.8846893322043142, 10);
    });

    it('estimates the difference and lift intervals within Monte Carlo error', () => {
        expect(result.absoluteDifference.credibleInterval.lower).toBeCloseTo(-0.0152, 2);
        expect(result.absoluteDifference.credibleInterval.upper).toBeCloseTo(0.0632, 2);
        expect(result.relativeLift.median).toBeCloseTo(0.237, 2);
        expect(result.relativeLift.credibleInterval.lower).toBeCloseTo(-0.1256, 2);
        expect(result.relativeLift.credibleInterval.upper).toBeCloseTo(0.76, 2);
    });

    it('calls 88% inconclusive rather than declaring a winner', () => {
        expect(result.verdict).toBe('inconclusive');
    });

    it('gives exactly 0.5 for identical data', () => {
        const equal = compareConversion({ visitors: 1000, conversions: 100 }, { visitors: 1000, conversions: 100 });
        expect(equal.probabilityTreatmentBeatsControl).toBeCloseTo(0.5, 10);
        expect(equal.relativeLift.median).toBeCloseTo(0, 2);
        expect(equal.verdict).toBe('inconclusive');
    });

    it('reports a likely winner in either direction only with enough evidence', () => {
        expect(
            compareConversion({ visitors: 1000, conversions: 100 }, { visitors: 1000, conversions: 140 }).verdict,
        ).toBe('treatment_likely_better');
        expect(
            compareConversion({ visitors: 1000, conversions: 140 }, { visitors: 1000, conversions: 100 }).verdict,
        ).toBe('control_likely_better');
    });

    it('withholds a verdict below the minimum sample, however strong the probability', () => {
        const small = compareConversion({ visitors: 10, conversions: 0 }, { visitors: 10, conversions: 3 });
        expect(small.probabilityTreatmentBeatsControl).toBeCloseTo(0.9548872180451128, 10);
        expect(small.verdict).toBe('insufficient_data');
    });

    it('handles zero conversions without inventing a lift', () => {
        const none = compareConversion({ visitors: 200, conversions: 0 }, { visitors: 200, conversions: 0 });
        expect(none.observedAbsoluteDifference).toBe(0);
        expect(none.observedRelativeLift).toBeNull();
        expect(none.probabilityTreatmentBeatsControl).toBeCloseTo(0.5, 10);
        expect(none.verdict).toBe('insufficient_data');
    });

    it('handles empty arms by reporting the prior and no observed rate', () => {
        const empty = compareConversion({ visitors: 0, conversions: 0 }, { visitors: 0, conversions: 0 });
        expect(empty.control.observedRate).toBeNull();
        expect(empty.observedAbsoluteDifference).toBeNull();
        expect(empty.control.posteriorMean).toBe(0.5);
        expect(empty.verdict).toBe('insufficient_data');
    });

    it('is reproducible for a given seed', () => {
        const again = compareConversion({ visitors: 500, conversions: 50 }, { visitors: 500, conversions: 62 });
        expect(again).toEqual(result);
        const otherSeed = compareConversion(
            { visitors: 500, conversions: 50 },
            { visitors: 500, conversions: 62 },
            { seed: 7 },
        );
        expect(otherSeed.relativeLift.median).not.toBe(result.relativeLift.median);
        expect(otherSeed.probabilityTreatmentBeatsControl).toBe(result.probabilityTreatmentBeatsControl);
    });

    it.each([
        [{ visitors: 10, conversions: 11 }, 'exceed visitors'],
        [{ visitors: -1, conversions: 0 }, 'visitors must be a non-negative integer'],
        [{ visitors: 10.5, conversions: 1 }, 'visitors must be a non-negative integer'],
        [{ visitors: 10, conversions: -2 }, 'conversions must be a non-negative integer'],
        [{ visitors: 10, conversions: Number.NaN }, 'conversions must be a non-negative integer'],
    ])('rejects impossible counts %j', (counts, message) => {
        expect(() => compareConversion(counts, { visitors: 10, conversions: 1 })).toThrow(InvalidDataError);
        expect(() => compareConversion({ visitors: 10, conversions: 1 }, counts)).toThrow(message);
    });

    it.each([0, -5, 1.5, Number.NaN, Number.POSITIVE_INFINITY, 2 ** 53, 10_000_001])(
        'rejects %d draws before sampling',
        (draws) => {
            // Given
            const arm = { visitors: 100, conversions: 10 };

            // When / Then
            expect(() => compareConversion(arm, arm, { draws })).toThrow('draws must be a positive integer');
        },
    );
});
