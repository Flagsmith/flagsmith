import { betaQuantile, probabilityBExceedsA } from './beta';
import { sortedQuantile } from './descriptive';
import { InvalidDataError } from './invalid-data-error';
import { createRandom, sampleBeta } from './random';

/** Uniform Beta(1, 1) prior: every conversion rate is equally plausible before seeing data. */
export const PRIOR = { alpha: 1, beta: 1 } as const;
export const CREDIBLE_LEVEL = 0.95;
/** Mirrors Flagsmith's collecting-data floor: 50 visitors and 5 conversions in each arm. */
export const MINIMUM_SAMPLE = { visitors: 50, conversions: 5 } as const;
export const DECISION_THRESHOLD = 0.95;

const DEFAULT_DRAWS = 100_000;
/** Caps the Monte Carlo work so a mistaken draws argument cannot hang the caller. */
const MAX_DRAWS = 10_000_000;
const DEFAULT_SEED = 20_261_126;

export type ArmCounts = { visitors: number; conversions: number };
export type Interval = { lower: number; upper: number };

export type ArmPosterior = ArmCounts & {
    observedRate: number | null;
    posteriorMean: number;
    credibleInterval: Interval;
};

export type Verdict = 'insufficient_data' | 'treatment_likely_better' | 'control_likely_better' | 'inconclusive';

export type ConversionComparison = {
    control: ArmPosterior;
    treatment: ArmPosterior;
    observedAbsoluteDifference: number | null;
    observedRelativeLift: number | null;
    absoluteDifference: { median: number; credibleInterval: Interval };
    relativeLift: { median: number; credibleInterval: Interval };
    probabilityTreatmentBeatsControl: number;
    verdict: Verdict;
    method: { prior: typeof PRIOR; credibleLevel: number; draws: number; seed: number };
};

export function validateArmCounts(name: string, { visitors, conversions }: ArmCounts): void {
    if (!Number.isSafeInteger(visitors) || visitors < 0) {
        throw new InvalidDataError(`${name}: visitors must be a non-negative integer (got ${visitors}).`);
    }
    if (!Number.isSafeInteger(conversions) || conversions < 0) {
        throw new InvalidDataError(`${name}: conversions must be a non-negative integer (got ${conversions}).`);
    }
    if (conversions > visitors) {
        throw new InvalidDataError(`${name}: conversions (${conversions}) exceed visitors (${visitors}).`);
    }
}

function posteriorOf(counts: ArmCounts) {
    return { alpha: PRIOR.alpha + counts.conversions, beta: PRIOR.beta + counts.visitors - counts.conversions };
}

function summariseArm(counts: ArmCounts): ArmPosterior {
    const { alpha, beta } = posteriorOf(counts);
    const tail = (1 - CREDIBLE_LEVEL) / 2;
    return {
        ...counts,
        observedRate: counts.visitors === 0 ? null : counts.conversions / counts.visitors,
        posteriorMean: alpha / (alpha + beta),
        credibleInterval: { lower: betaQuantile(tail, alpha, beta), upper: betaQuantile(1 - tail, alpha, beta) },
    };
}

function summariseDraws(draws: number[]) {
    draws.sort((a, b) => a - b);
    const tail = (1 - CREDIBLE_LEVEL) / 2;
    return {
        median: sortedQuantile(draws, 0.5),
        credibleInterval: { lower: sortedQuantile(draws, tail), upper: sortedQuantile(draws, 1 - tail) },
    };
}

function decide(control: ArmCounts, treatment: ArmCounts, probability: number): Verdict {
    const enoughData = [control, treatment].every(
        (arm) => arm.visitors >= MINIMUM_SAMPLE.visitors && arm.conversions >= MINIMUM_SAMPLE.conversions,
    );
    if (!enoughData) {
        return 'insufficient_data';
    }
    if (probability >= DECISION_THRESHOLD) {
        return 'treatment_likely_better';
    }
    return probability <= 1 - DECISION_THRESHOLD ? 'control_likely_better' : 'inconclusive';
}

/**
 * Beta-binomial comparison of two conversion rates. The probability that treatment beats control is
 * exact; the intervals for the difference and lift come from seeded Monte Carlo draws of both
 * posteriors, so the same input always gives the same output.
 */
export function compareConversion(
    control: ArmCounts,
    treatment: ArmCounts,
    { draws = DEFAULT_DRAWS, seed = DEFAULT_SEED }: { draws?: number; seed?: number } = {},
): ConversionComparison {
    validateArmCounts('control', control);
    validateArmCounts('treatment', treatment);
    if (!Number.isSafeInteger(draws) || draws < 1 || draws > MAX_DRAWS) {
        throw new InvalidDataError(`draws must be a positive integer no larger than ${MAX_DRAWS} (got ${draws}).`);
    }

    const controlPosterior = posteriorOf(control);
    const treatmentPosterior = posteriorOf(treatment);
    const probability = probabilityBExceedsA(
        controlPosterior.alpha,
        controlPosterior.beta,
        treatmentPosterior.alpha,
        treatmentPosterior.beta,
    );

    const random = createRandom(seed);
    const differences: number[] = [];
    const lifts: number[] = [];
    for (let i = 0; i < draws; i++) {
        const controlRate = sampleBeta(controlPosterior.alpha, controlPosterior.beta, random);
        const treatmentRate = sampleBeta(treatmentPosterior.alpha, treatmentPosterior.beta, random);
        differences.push(treatmentRate - controlRate);
        lifts.push((treatmentRate - controlRate) / controlRate);
    }

    const controlArm = summariseArm(control);
    const treatmentArm = summariseArm(treatment);
    const observedDifference =
        controlArm.observedRate === null || treatmentArm.observedRate === null
            ? null
            : treatmentArm.observedRate - controlArm.observedRate;

    return {
        control: controlArm,
        treatment: treatmentArm,
        observedAbsoluteDifference: observedDifference,
        observedRelativeLift:
            observedDifference === null || !controlArm.observedRate
                ? null
                : observedDifference / controlArm.observedRate,
        absoluteDifference: summariseDraws(differences),
        relativeLift: summariseDraws(lifts),
        probabilityTreatmentBeatsControl: probability,
        verdict: decide(control, treatment, probability),
        method: { prior: PRIOR, credibleLevel: CREDIBLE_LEVEL, draws, seed },
    };
}
