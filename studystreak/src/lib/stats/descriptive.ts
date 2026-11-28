import { InvalidDataError } from './invalid-data-error';

export function mean(values: readonly number[]): number | null {
    return values.length === 0 ? null : values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function median(values: readonly number[]): number | null {
    if (values.length === 0) {
        return null;
    }
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 1 ? sorted[middle]! : (sorted[middle - 1]! + sorted[middle]!) / 2;
}

/**
 * Quantile of already sorted values, with linear interpolation (the default in NumPy and R type 7). Empty input and
 * probabilities outside [0, 1] are rejected rather than returning NaN.
 */
export function sortedQuantile(sorted: readonly number[], probability: number): number {
    if (sorted.length === 0) {
        throw new InvalidDataError('Cannot take a quantile of no values.');
    }
    if (!(probability >= 0 && probability <= 1)) {
        throw new InvalidDataError(`The quantile probability must be between 0 and 1 (got ${probability}).`);
    }
    const position = (sorted.length - 1) * probability;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    return sorted[lower]! + (sorted[upper]! - sorted[lower]!) * (position - lower);
}
