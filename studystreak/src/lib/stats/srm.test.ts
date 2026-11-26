import { describe, expect, it } from 'vitest';
import { checkSampleRatio } from './srm';

// p-values from scipy.stats.chi2.sf(chi_square, 1).
describe('checkSampleRatio', () => {
    it.each([
        [500, 500, 0, 1, 'ok'],
        [460, 540, 6.4, 0.01141203638600166, 'ok'],
        [440, 560, 14.4, 0.00014780231033445398, 'mismatch'],
        [40, 60, 4, 0.04550026389635857, 'ok'],
    ])('control %d / treatment %d', (control, treatment, chiSquare, pValue, status) => {
        const check = checkSampleRatio(control, treatment);

        expect(check).toMatchObject({ status, control, treatment, expectedShare: 0.5 });
        if (check.status === 'not_checked') {
            throw new Error('expected a check');
        }
        expect(check.expectedControl).toBe((control + treatment) / 2);
        expect(check.chiSquare).toBeCloseTo(chiSquare, 10);
        expect(check.pValue).toBeCloseTo(pValue, 6);
    });

    it('does not check fewer than 100 visitors', () => {
        expect(checkSampleRatio(30, 60)).toMatchObject({ status: 'not_checked', control: 30, treatment: 60 });
        expect(checkSampleRatio(0, 0).status).toBe('not_checked');
    });

    it('supports other configured splits', () => {
        const check = checkSampleRatio(800, 200, 0.2);
        expect(check).toMatchObject({ status: 'ok', expectedTreatment: 200, expectedControl: 800, chiSquare: 0 });
    });
});
