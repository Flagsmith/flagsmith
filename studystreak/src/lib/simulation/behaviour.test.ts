import { describe, expect, it } from 'vitest';
import { median } from '@/lib/stats/descriptive';
import { simulateBehaviour, simulatedVisitorId } from './behaviour';
import { DEFAULT_OPTIONS } from './options';

const SEED = 123;
const visitors = Array.from({ length: 20_000 }, (_, index) => index);

describe('simulatedVisitorId', () => {
    it('creates unique sim- identities for a run', () => {
        const ids = visitors.map((index) => simulatedVisitorId(SEED, index));
        expect(new Set(ids).size).toBe(ids.length);
        expect(ids.every((id) => id.startsWith('sim-'))).toBe(true);
        expect(simulatedVisitorId(SEED, 7)).toBe('sim-s123-00007');
    });

    it('keeps runs with different seeds apart', () => {
        expect(simulatedVisitorId(1, 0)).not.toBe(simulatedVisitorId(2, 0));
    });
});

describe('simulateBehaviour', () => {
    it('is reproducible for the same seed and visitor', () => {
        expect(simulateBehaviour(SEED, 42, 'control', DEFAULT_OPTIONS)).toEqual(
            simulateBehaviour(SEED, 42, 'control', DEFAULT_OPTIONS),
        );
    });

    it('depends on the seed', () => {
        const run = (seed: number) =>
            visitors.slice(0, 200).map((index) => simulateBehaviour(seed, index, 'control', DEFAULT_OPTIONS));
        expect(run(1)).not.toEqual(run(2));
    });

    it('only signs up visitors who clicked', () => {
        for (const index of visitors.slice(0, 2000)) {
            const behaviour = simulateBehaviour(SEED, index, 'social_proof', DEFAULT_OPTIONS);
            if (behaviour.signedUp) {
                expect(behaviour.clickedAfterSeconds).not.toBeNull();
            }
        }
    });

    it('uses the same draws in both variants, so the higher rate never loses a click', () => {
        for (const index of visitors.slice(0, 2000)) {
            const control = simulateBehaviour(SEED, index, 'control', DEFAULT_OPTIONS);
            const treatment = simulateBehaviour(SEED, index, 'social_proof', DEFAULT_OPTIONS);
            if (control.clickedAfterSeconds !== null) {
                expect(treatment).toEqual(control);
            }
        }
    });

    it.each([
        ['control', 0.1],
        ['social_proof', 0.12],
    ] as const)('produces about the configured %s signup rate over many visitors', (variant, rate) => {
        const outcomes = visitors.map((index) => simulateBehaviour(SEED, index, variant, DEFAULT_OPTIONS));
        const signupRate = outcomes.filter((outcome) => outcome.signedUp).length / outcomes.length;
        const clickRate = outcomes.filter((outcome) => outcome.clickedAfterSeconds !== null).length / outcomes.length;

        expect(signupRate).toBeGreaterThan(rate - 0.01);
        expect(signupRate).toBeLessThan(rate + 0.01);
        expect(clickRate).toBeCloseTo(rate / DEFAULT_OPTIONS.clickToSignupRate, 1);
    });

    it('produces positive, bounded click times around the median', () => {
        const times = visitors
            .map((index) => simulateBehaviour(SEED, index, 'social_proof', DEFAULT_OPTIONS).clickedAfterSeconds)
            .filter((seconds): seconds is number => seconds !== null);

        expect(Math.min(...times)).toBeGreaterThanOrEqual(0);
        expect(Math.max(...times)).toBeLessThanOrEqual(600);
        expect(median(times)).toBeGreaterThan(7);
        expect(median(times)).toBeLessThan(9);
    });
});
