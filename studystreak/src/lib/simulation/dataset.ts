import { InvalidDataError } from '@/lib/stats/invalid-data-error';

export const SIMULATED_ID_PREFIX = 'sim-';
export const VARIANTS = ['control', 'social_proof'] as const;
export type Variant = (typeof VARIANTS)[number];

export type SimulatedVisitor = {
    visitorId: string;
    variant: Variant;
    /** Seconds from first exposure to first signup click, or null if the visitor never clicked. */
    clickedAfterSeconds: number | null;
    signedUp: boolean;
};

export type SimulatedDataset = {
    kind: 'simulated';
    environment: 'simulation';
    seed: number;
    generatedAt: string;
    visitors: SimulatedVisitor[];
};

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;

function parseVisitor(raw: unknown, index: number): SimulatedVisitor {
    const where = `visitors[${index}]`;
    if (!isRecord(raw)) {
        throw new InvalidDataError(`${where} must be an object.`);
    }
    const { visitorId, variant, clickedAfterSeconds, signedUp } = raw;
    if (typeof visitorId !== 'string' || !visitorId.startsWith(SIMULATED_ID_PREFIX)) {
        throw new InvalidDataError(`${where}.visitorId must start with "${SIMULATED_ID_PREFIX}".`);
    }
    if (!VARIANTS.includes(variant as Variant)) {
        throw new InvalidDataError(`${where}.variant must be one of ${VARIANTS.join(', ')}.`);
    }
    if (
        clickedAfterSeconds !== null &&
        (typeof clickedAfterSeconds !== 'number' || !Number.isFinite(clickedAfterSeconds) || clickedAfterSeconds < 0)
    ) {
        throw new InvalidDataError(`${where}.clickedAfterSeconds must be null or a non-negative number.`);
    }
    if (typeof signedUp !== 'boolean') {
        throw new InvalidDataError(`${where}.signedUp must be a boolean.`);
    }
    // In the app a signup can only start from the CTA, so a signup without a click is impossible.
    if (signedUp && clickedAfterSeconds === null) {
        throw new InvalidDataError(`${where} signed up without clicking Sign Up.`);
    }
    return { visitorId, variant: variant as Variant, clickedAfterSeconds, signedUp };
}

/** Validates untrusted JSON as a simulated dataset. Nothing is defaulted, corrected or dropped. */
export function parseSimulatedDataset(raw: unknown): SimulatedDataset {
    if (!isRecord(raw)) {
        throw new InvalidDataError('The dataset must be a JSON object.');
    }
    if (raw.kind !== 'simulated' || raw.environment !== 'simulation') {
        throw new InvalidDataError(
            'Only datasets marked kind "simulated" from the "simulation" environment are accepted.',
        );
    }
    if (!Number.isSafeInteger(raw.seed)) {
        throw new InvalidDataError('seed must be an integer.');
    }
    if (typeof raw.generatedAt !== 'string' || Number.isNaN(Date.parse(raw.generatedAt))) {
        throw new InvalidDataError('generatedAt must be an ISO 8601 timestamp.');
    }
    if (!Array.isArray(raw.visitors)) {
        throw new InvalidDataError('visitors must be an array.');
    }
    const visitors = raw.visitors.map(parseVisitor);
    const ids = new Set(visitors.map((visitor) => visitor.visitorId));
    if (ids.size !== visitors.length) {
        throw new InvalidDataError('visitorId values must be unique.');
    }
    return {
        kind: 'simulated',
        environment: 'simulation',
        seed: raw.seed as number,
        generatedAt: raw.generatedAt,
        visitors,
    };
}
