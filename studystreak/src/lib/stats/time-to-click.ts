import { mean, median } from './descriptive';
import { InvalidDataError } from './invalid-data-error';

export type TimeToClickSummary = {
    visitors: number;
    clickers: number;
    clickerMean: number | null;
    clickerMedian: number | null;
    /** What Flagsmith's official Mean metric computes: non-clickers count as 0 seconds. */
    zeroFilledMean: number | null;
};

/** Time to first signup click, among visitors who actually clicked. */
export function summariseTimeToClick(
    name: string,
    visitors: number,
    clickSeconds: readonly number[],
): TimeToClickSummary {
    if (!Number.isSafeInteger(visitors) || visitors < 0) {
        throw new InvalidDataError(`${name}: visitors must be a non-negative integer (got ${visitors}).`);
    }
    if (clickSeconds.length > visitors) {
        throw new InvalidDataError(`${name}: ${clickSeconds.length} clickers exceed ${visitors} visitors.`);
    }
    const invalid = clickSeconds.find((seconds) => !Number.isFinite(seconds) || seconds < 0);
    if (invalid !== undefined) {
        throw new InvalidDataError(`${name}: click times must be finite and non-negative (got ${invalid}).`);
    }
    const total = clickSeconds.reduce((sum, seconds) => sum + seconds, 0);
    if (!Number.isFinite(total)) {
        throw new InvalidDataError(`${name}: the total click time is too large to summarise.`);
    }
    return {
        visitors,
        clickers: clickSeconds.length,
        clickerMean: mean(clickSeconds),
        clickerMedian: median(clickSeconds),
        zeroFilledMean: visitors === 0 ? null : total / visitors,
    };
}
