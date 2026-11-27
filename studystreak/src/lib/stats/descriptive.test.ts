import { describe, expect, it } from 'vitest';
import { mean, median, sortedQuantile } from './descriptive';
import { InvalidDataError } from './invalid-data-error';

describe('sortedQuantile', () => {
    it.each([
        [0, 1],
        [0.5, 2.5],
        [0.25, 1.75],
        [1, 4],
    ])('interpolates quantile %d of [1, 2, 3, 4] like NumPy', (probability, expected) => {
        expect(sortedQuantile([1, 2, 3, 4], probability)).toBe(expected);
    });

    it('returns the only value of a single-element input', () => {
        expect(sortedQuantile([7], 0.975)).toBe(7);
    });

    it('rejects an empty input instead of returning NaN', () => {
        // Given
        const empty: number[] = [];

        // When / Then
        expect(() => sortedQuantile(empty, 0.5)).toThrow(InvalidDataError);
    });

    it.each([-0.01, 1.01, Number.NaN])('rejects the probability %d', (probability) => {
        expect(() => sortedQuantile([1, 2], probability)).toThrow(InvalidDataError);
    });
});

describe('mean and median', () => {
    it('return null for no values', () => {
        expect(mean([])).toBeNull();
        expect(median([])).toBeNull();
    });
});
