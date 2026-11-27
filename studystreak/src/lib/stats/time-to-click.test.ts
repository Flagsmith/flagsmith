import { describe, expect, it } from 'vitest';
import { InvalidDataError } from './invalid-data-error';
import { summariseTimeToClick } from './time-to-click';

describe('summariseTimeToClick', () => {
    it('summarises clickers only, and separately shows the zero-filled mean', () => {
        expect(summariseTimeToClick('control', 10, [2, 4, 9])).toEqual({
            visitors: 10,
            clickers: 3,
            clickerMean: 5,
            clickerMedian: 4,
            zeroFilledMean: 1.5,
        });
    });

    it('takes the middle pair for an even number of clickers', () => {
        expect(summariseTimeToClick('control', 4, [10, 1, 3, 8]).clickerMedian).toBe(5.5);
    });

    it('reports no clicker statistics when nobody clicked', () => {
        expect(summariseTimeToClick('control', 25, [])).toEqual({
            visitors: 25,
            clickers: 0,
            clickerMean: null,
            clickerMedian: null,
            zeroFilledMean: 0,
        });
    });

    it('handles an empty arm', () => {
        expect(summariseTimeToClick('control', 0, [])).toMatchObject({
            clickers: 0,
            clickerMean: null,
            zeroFilledMean: null,
        });
    });

    it.each([[[-1]], [[Number.NaN]], [[Number.POSITIVE_INFINITY]]])('rejects invalid click times %j', (times) => {
        expect(() => summariseTimeToClick('control', 5, times)).toThrow(InvalidDataError);
    });

    it('rejects more clickers than visitors', () => {
        expect(() => summariseTimeToClick('control', 1, [1, 2])).toThrow('exceed');
    });

    it('rejects finite click times whose total overflows', () => {
        // Given
        const times = [Number.MAX_VALUE, Number.MAX_VALUE];

        // When / Then
        expect(() => summariseTimeToClick('control', 2, times)).toThrow('too large to summarise');
    });
});
