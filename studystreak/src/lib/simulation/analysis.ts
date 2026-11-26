import { compareConversion, type ConversionComparison } from '@/lib/stats/conversion';
import { checkSampleRatio, type SampleRatioCheck } from '@/lib/stats/srm';
import { summariseTimeToClick, type TimeToClickSummary } from '@/lib/stats/time-to-click';
import type { SimulatedDataset, Variant } from './dataset';

export const SIMULATED_DATA_LABEL = 'SIMULATED DATA — SUPPLEMENTARY ANALYSIS';

export type SupplementaryAnalysis = {
    label: typeof SIMULATED_DATA_LABEL;
    seed: number;
    generatedAt: string;
    totalVisitors: number;
    signedUp: ConversionComparison;
    clickedSignUp: ConversionComparison;
    sampleRatio: SampleRatioCheck;
    timeToClick: Record<Variant, TimeToClickSummary>;
};

export function analyseSimulatedDataset(dataset: SimulatedDataset): SupplementaryAnalysis {
    const byVariant = (variant: Variant) => dataset.visitors.filter((visitor) => visitor.variant === variant);
    const control = byVariant('control');
    const treatment = byVariant('social_proof');
    const counts = (visitors: typeof control, converted: (visitor: (typeof control)[number]) => boolean) => ({
        visitors: visitors.length,
        conversions: visitors.filter(converted).length,
    });
    const clickTimes = (visitors: typeof control) =>
        visitors.flatMap((visitor) => (visitor.clickedAfterSeconds === null ? [] : [visitor.clickedAfterSeconds]));

    return {
        label: SIMULATED_DATA_LABEL,
        seed: dataset.seed,
        generatedAt: dataset.generatedAt,
        totalVisitors: dataset.visitors.length,
        signedUp: compareConversion(
            counts(control, (visitor) => visitor.signedUp),
            counts(treatment, (visitor) => visitor.signedUp),
        ),
        clickedSignUp: compareConversion(
            counts(control, (visitor) => visitor.clickedAfterSeconds !== null),
            counts(treatment, (visitor) => visitor.clickedAfterSeconds !== null),
        ),
        sampleRatio: checkSampleRatio(control.length, treatment.length, 0.5),
        timeToClick: {
            control: summariseTimeToClick('control', control.length, clickTimes(control)),
            social_proof: summariseTimeToClick('social_proof', treatment.length, clickTimes(treatment)),
        },
    };
}
