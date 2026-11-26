import { describe, expect, it } from 'vitest';
import { betaCdf, betaQuantile, logGamma, probabilityBExceedsA } from './beta';

// Reference values from SciPy 1.18.1 (scipy.stats.beta) and mpmath 1.4.1 numerical integration.
describe('logGamma', () => {
    it.each([
        [1, 0],
        [5, Math.log(24)],
        [0.5, Math.log(Math.sqrt(Math.PI))],
        [101, 363.73937555556347],
    ])('logGamma(%d)', (x, expected) => {
        expect(logGamma(x)).toBeCloseTo(expected, 9);
    });
});

describe('betaCdf', () => {
    it('matches SciPy', () => {
        expect(betaCdf(0.3, 2, 5)).toBeCloseTo(0.579825, 10);
    });

    it('is bounded by 0 and 1', () => {
        expect(betaCdf(0, 3, 4)).toBe(0);
        expect(betaCdf(1, 3, 4)).toBe(1);
    });
});

describe('betaQuantile', () => {
    it.each([
        [0.5, 2, 3, 0.3857275681323895],
        [0.025, 51, 451, 0.07673686025971445],
        [0.975, 51, 451, 0.12945448809721105],
        [0.025, 1, 11, 0.002298972213814267],
        [0.975, 4, 8, 0.6097425595724212],
    ])('quantile %d of Beta(%d, %d) matches SciPy', (probability, a, b, expected) => {
        expect(betaQuantile(probability, a, b)).toBeCloseTo(expected, 9);
    });
});

describe('probabilityBExceedsA', () => {
    it.each([
        [51, 451, 63, 439, 0.8846893322043142],
        [1, 11, 4, 8, 0.9548872180451128],
        [101, 901, 101, 901, 0.5],
    ])('P(Beta(%d,%d) < Beta(%d,%d)) matches numerical integration', (aA, bA, aB, bB, expected) => {
        expect(probabilityBExceedsA(aA, bA, aB, bB)).toBeCloseTo(expected, 10);
    });

    it('is symmetric: P(B > A) + P(A > B) = 1', () => {
        expect(probabilityBExceedsA(51, 451, 63, 439) + probabilityBExceedsA(63, 439, 51, 451)).toBeCloseTo(1, 12);
    });

    it('requires an integer alphaB', () => {
        expect(() => probabilityBExceedsA(1, 1, 1.5, 1)).toThrow(RangeError);
    });
});
