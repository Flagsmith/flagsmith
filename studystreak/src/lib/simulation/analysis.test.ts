import { describe, expect, it } from 'vitest';
import { analyseSimulatedDataset, SIMULATED_DATA_LABEL } from './analysis';
import { simulatedDataset } from '@/test/simulated-dataset';
import type { SimulatedVisitor, Variant } from './dataset';

function visitors(variant: Variant, count: number, clickTimes: number[], signups: number): SimulatedVisitor[] {
    return Array.from({ length: count }, (_, index) => ({
        visitorId: `sim-${variant}-${index}`,
        variant,
        clickedAfterSeconds: clickTimes[index] ?? null,
        signedUp: index < signups,
    }));
}

const dataset = simulatedDataset([
    ...visitors('control', 500, [...Array.from({ length: 80 }, (_, i) => 10 + i)], 50),
    ...visitors('social_proof', 500, [...Array.from({ length: 90 }, (_, i) => 5 + i)], 62),
]);

describe('analyseSimulatedDataset', () => {
    const analysis = analyseSimulatedDataset(dataset);

    it('labels the result as simulated supplementary analysis', () => {
        expect(analysis.label).toBe(SIMULATED_DATA_LABEL);
        expect(analysis.label).toBe('SIMULATED DATA — SUPPLEMENTARY ANALYSIS');
        expect(analysis).toMatchObject({ seed: 7, totalVisitors: 1000 });
    });

    it('compares signups between the variants', () => {
        expect(analysis.signedUp.control).toMatchObject({ visitors: 500, conversions: 50 });
        expect(analysis.signedUp.treatment).toMatchObject({ visitors: 500, conversions: 62 });
        expect(analysis.signedUp.probabilityTreatmentBeatsControl).toBeCloseTo(0.8846893322043142, 10);
    });

    it('compares click-through between the variants', () => {
        expect(analysis.clickedSignUp.control).toMatchObject({ visitors: 500, conversions: 80 });
        expect(analysis.clickedSignUp.treatment).toMatchObject({ visitors: 500, conversions: 90 });
    });

    it('checks the split against 50/50', () => {
        expect(analysis.sampleRatio).toMatchObject({ status: 'ok', control: 500, treatment: 500, chiSquare: 0 });
    });

    it('summarises time to click among clickers only', () => {
        expect(analysis.timeToClick.control).toMatchObject({ clickers: 80, clickerMean: 49.5, clickerMedian: 49.5 });
        expect(analysis.timeToClick.social_proof).toMatchObject({
            clickers: 90,
            clickerMean: 49.5,
            clickerMedian: 49.5,
        });
        expect(analysis.timeToClick.control.zeroFilledMean).toBeCloseTo((80 * 49.5) / 500, 12);
    });

    it('handles an empty dataset', () => {
        const empty = analyseSimulatedDataset({ ...dataset, visitors: [] });
        expect(empty.totalVisitors).toBe(0);
        expect(empty.signedUp.verdict).toBe('insufficient_data');
        expect(empty.sampleRatio.status).toBe('not_checked');
        expect(empty.timeToClick.control.clickerMean).toBeNull();
    });
});
