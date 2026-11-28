import type { Verdict } from '@/lib/stats/conversion';

const percent = new Intl.NumberFormat('en-GB', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
});
const signedPercent = new Intl.NumberFormat('en-GB', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    signDisplay: 'exceptZero',
});
const signedPoints = new Intl.NumberFormat('en-GB', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    signDisplay: 'exceptZero',
});

export const formatPercent = (value: number | null) => (value === null ? 'n/a' : percent.format(value));
export const formatSignedPercent = (value: number | null) => (value === null ? 'n/a' : signedPercent.format(value));
export const formatPercentagePoints = (value: number | null) =>
    value === null ? 'n/a' : `${signedPoints.format(value * 100)} pp`;
export const formatSeconds = (value: number | null) => (value === null ? 'n/a' : `${value.toFixed(1)} s`);
export const formatInterval = (interval: { lower: number; upper: number }, format: (value: number) => string): string =>
    `${format(interval.lower)} to ${format(interval.upper)}`;

export const VERDICT_TEXT: Record<Verdict, string> = {
    insufficient_data: 'Not enough data (each variant needs 50 visitors and 5 conversions)',
    treatment_likely_better: 'Social proof likely better (at least 95% probability)',
    control_likely_better: 'Control likely better (at most 5% probability social proof is better)',
    inconclusive: 'Inconclusive (between 5% and 95% probability)',
};
