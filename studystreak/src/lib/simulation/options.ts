import { InvalidDataError } from '@/lib/stats/invalid-data-error';

export type SimulationOptions = {
    visitors: number;
    seed: number;
    signupRate: { control: number; social_proof: number };
    /** Share of clickers who go on to complete signup; sets the click rate as signupRate / this. */
    clickToSignupRate: number;
    medianClickSeconds: number;
};

export const DEFAULT_OPTIONS: SimulationOptions = {
    visitors: 1000,
    seed: 20_261_129,
    signupRate: { control: 0.1, social_proof: 0.12 },
    clickToSignupRate: 0.6,
    medianClickSeconds: 8,
};

const FLAGS: Record<string, (options: SimulationOptions, value: number) => void> = {
    '--visitors': (options, value) => (options.visitors = value),
    '--seed': (options, value) => (options.seed = value),
    '--control-signup-rate': (options, value) => (options.signupRate.control = value),
    '--social-proof-signup-rate': (options, value) => (options.signupRate.social_proof = value),
    '--click-to-signup-rate': (options, value) => (options.clickToSignupRate = value),
    '--median-click-seconds': (options, value) => (options.medianClickSeconds = value),
};

export const USAGE = `Usage: npm run simulate:traffic -- [${Object.keys(FLAGS)
    .map((flag) => `${flag} <number>`)
    .join('] [')}]`;

/** Parses `--name value` pairs. Unknown flags and invalid values are errors, never ignored or clamped. */
export function parseSimulationOptions(args: readonly string[]): SimulationOptions {
    const options: SimulationOptions = { ...DEFAULT_OPTIONS, signupRate: { ...DEFAULT_OPTIONS.signupRate } };
    for (let i = 0; i < args.length; i += 2) {
        const flag = args[i]!;
        const apply = FLAGS[flag];
        if (!apply) {
            throw new InvalidDataError(`Unknown option ${flag}. ${USAGE}`);
        }
        const raw = args[i + 1];
        const value = Number(raw);
        if (raw === undefined || raw.trim() === '' || !Number.isFinite(value)) {
            throw new InvalidDataError(`${flag} needs a number (got ${raw ?? 'nothing'}).`);
        }
        apply(options, value);
    }
    validateSimulationOptions(options);
    return options;
}

export function validateSimulationOptions(options: SimulationOptions): void {
    const { visitors, seed, signupRate, clickToSignupRate, medianClickSeconds } = options;
    if (!Number.isSafeInteger(visitors) || visitors < 1 || visitors > 10_000) {
        throw new InvalidDataError('--visitors must be a whole number from 1 to 10,000.');
    }
    if (!Number.isSafeInteger(seed) || seed < 0 || seed > 0xffffffff) {
        throw new InvalidDataError('--seed must be a whole number from 0 to 4,294,967,295.');
    }
    if (!(clickToSignupRate > 0 && clickToSignupRate <= 1)) {
        throw new InvalidDataError('--click-to-signup-rate must be greater than 0 and at most 1.');
    }
    for (const [variant, rate] of Object.entries(signupRate)) {
        if (!(rate >= 0 && rate <= 1)) {
            throw new InvalidDataError(`The ${variant} signup rate must be between 0 and 1.`);
        }
        if (rate / clickToSignupRate > 1) {
            throw new InvalidDataError(
                `The ${variant} signup rate (${rate}) needs a click rate above 100% with --click-to-signup-rate ${clickToSignupRate}.`,
            );
        }
    }
    if (!(medianClickSeconds > 0 && medianClickSeconds <= 600)) {
        throw new InvalidDataError('--median-click-seconds must be greater than 0 and at most 600.');
    }
}
