import { createRandom } from '@/lib/stats/random';
import type { Variant } from './dataset';
import type { SimulationOptions } from './options';

// Spread of the log-normal time-to-click distribution: most clicks land between about a third and
// three times the median, with a long tail of slower visitors.
const CLICK_TIME_LOG_SPREAD = 0.8;
const MAX_CLICK_SECONDS = 600;

export function simulatedVisitorId(seed: number, index: number): string {
    return `sim-s${seed}-${String(index).padStart(5, '0')}`;
}

// A per-visitor seed, so each visitor's behaviour depends only on the run seed and their position,
// never on the order in which Flagsmith answered.
function visitorSeed(seed: number, index: number): number {
    let hash = (seed ^ Math.imul(index + 1, 0x9e3779b1)) >>> 0;
    hash = Math.imul(hash ^ (hash >>> 16), 0x85ebca6b) >>> 0;
    hash = Math.imul(hash ^ (hash >>> 13), 0xc2b2ae35) >>> 0;
    return (hash ^ (hash >>> 16)) >>> 0;
}

export type SimulatedBehaviour = { clickedAfterSeconds: number | null; signedUp: boolean };

/**
 * Decides a visitor's behaviour for the variant Flagsmith assigned. The same three random draws are
 * made whatever the variant, so a visitor behaves identically apart from the variant's rates.
 */
export function simulateBehaviour(
    seed: number,
    index: number,
    variant: Variant,
    options: Pick<SimulationOptions, 'signupRate' | 'clickToSignupRate' | 'medianClickSeconds'>,
): SimulatedBehaviour {
    const random = createRandom(visitorSeed(seed, index));
    const clickDraw = random();
    const signupDraw = random();
    const normal = Math.sqrt(-2 * Math.log(1 - random())) * Math.cos(2 * Math.PI * random());

    const clickRate = options.signupRate[variant] / options.clickToSignupRate;
    if (clickDraw >= clickRate) {
        return { clickedAfterSeconds: null, signedUp: false };
    }
    const seconds = Math.min(MAX_CLICK_SECONDS, options.medianClickSeconds * Math.exp(CLICK_TIME_LOG_SPREAD * normal));
    return {
        clickedAfterSeconds: Math.round(seconds * 10) / 10,
        signedUp: signupDraw < options.clickToSignupRate,
    };
}
