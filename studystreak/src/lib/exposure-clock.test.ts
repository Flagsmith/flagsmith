import { describe, expect, it } from 'vitest';
import {
    claimFirstSignupClick,
    claimFirstSignupClickAcrossTabs,
    createBrowserStore,
    type LockManagerLike,
    recordFirstExposure,
    secondsBetween,
} from './exposure-clock';

const VISITOR = 'visitor-1';
const mapStore = () => {
    const values = new Map<string, string>();
    return {
        getItem: (key: string) => values.get(key) ?? null,
        setItem: (key: string, value: string) => values.set(key, value),
    };
};

describe('secondsBetween', () => {
    it('rounds to tenths of a second', () => {
        expect(secondsBetween(1_000, 5_240)).toBe(4.2);
        expect(secondsBetween(0, 61_049)).toBe(61);
    });

    it('never goes negative if the clock moves backwards', () => {
        expect(secondsBetween(5_000, 1_000)).toBe(0);
    });
});

describe('claimFirstSignupClick', () => {
    it('measures from the first exposure, not later ones', () => {
        const store = mapStore();
        recordFirstExposure(store, VISITOR, 10_000);
        recordFirstExposure(store, VISITOR, 50_000);

        expect(claimFirstSignupClick(store, VISITOR, 72_500)).toBe(62.5);
    });

    it('counts only the first click per visitor', () => {
        const store = mapStore();
        recordFirstExposure(store, VISITOR, 0);

        expect(claimFirstSignupClick(store, VISITOR, 3_000)).toBe(3);
        expect(claimFirstSignupClick(store, VISITOR, 9_000)).toBeNull();
    });

    it('does not count a click from a visitor who was never exposed', () => {
        const store = mapStore();

        expect(claimFirstSignupClick(store, VISITOR, 3_000)).toBeNull();
        recordFirstExposure(store, VISITOR, 4_000);
        expect(claimFirstSignupClick(store, VISITOR, 6_000)).toBe(2);
    });

    it('ignores a corrupted exposure time', () => {
        const store = mapStore();
        store.setItem(`studystreak:${VISITOR}:first-exposure-ms`, 'not-a-number');

        expect(claimFirstSignupClick(store, VISITOR, 3_000)).toBeNull();
    });

    it('keeps visitors apart', () => {
        const store = mapStore();
        recordFirstExposure(store, 'a', 0);
        recordFirstExposure(store, 'b', 1_000);
        claimFirstSignupClick(store, 'a', 2_000);

        expect(claimFirstSignupClick(store, 'b', 2_000)).toBe(1);
    });
});

describe('createBrowserStore', () => {
    it('falls back to memory when storage throws', () => {
        const store = createBrowserStore(() => {
            throw new DOMException('denied', 'SecurityError');
        });
        recordFirstExposure(store, VISITOR, 0);

        expect(claimFirstSignupClick(store, VISITOR, 1_000)).toBe(1);
        expect(claimFirstSignupClick(store, VISITOR, 2_000)).toBeNull();
    });

    it('uses the provided storage when it works', () => {
        const values = new Map<string, string>();
        const storage = {
            getItem: (key: string) => values.get(key) ?? null,
            setItem: (key: string, value: string) => void values.set(key, value),
        } as Storage;
        recordFirstExposure(
            createBrowserStore(() => storage),
            VISITOR,
            123,
        );

        expect([...values.values()]).toEqual(['123']);
    });

    it('finds a value kept in memory when storage reads work but writes fail', () => {
        // Given: reads succeed (and miss), writes throw, as with a full quota
        const storage = {
            getItem: () => null,
            setItem: () => {
                throw new DOMException('full', 'QuotaExceededError');
            },
        } as unknown as Storage;
        const store = createBrowserStore(() => storage);

        // When
        recordFirstExposure(store, VISITOR, 0);

        // Then: the exposure is found and the click is counted only once
        expect(claimFirstSignupClick(store, VISITOR, 1_000)).toBe(1);
        expect(claimFirstSignupClick(store, VISITOR, 2_000)).toBeNull();
    });
});

describe('claimFirstSignupClickAcrossTabs', () => {
    // An exclusive lock per name, like the Web Locks API: callbacks for one name run one after another.
    function fakeLocks() {
        const tails = new Map<string, Promise<unknown>>();
        const names: string[] = [];
        const locks = {
            request: (name: string, callback: () => unknown) => {
                names.push(name);
                const run = (tails.get(name) ?? Promise.resolve()).then(() => callback());
                tails.set(
                    name,
                    run.catch(() => {}),
                );
                return run;
            },
        } as unknown as LockManagerLike;
        return { locks, names };
    }

    it('lets only one of two concurrent tabs claim the first click', async () => {
        // Given: two tabs sharing one storage, both exposed
        const shared = mapStore();
        recordFirstExposure(shared, VISITOR, 0);
        const { locks, names } = fakeLocks();

        // When: both claim at once
        const results = await Promise.all([
            claimFirstSignupClickAcrossTabs(shared, VISITOR, locks, () => 1_000),
            claimFirstSignupClickAcrossTabs(shared, VISITOR, locks, () => 1_500),
        ]);

        // Then
        expect(results.filter((seconds) => seconds !== null)).toEqual([1]);
        expect(names).toEqual([
            `studystreak:${VISITOR}:signup-click-claim`,
            `studystreak:${VISITOR}:signup-click-claim`,
        ]);
    });

    it('claims directly when the Web Locks API is unavailable', async () => {
        // Given
        const store = mapStore();
        recordFirstExposure(store, VISITOR, 0);

        // When / Then
        await expect(claimFirstSignupClickAcrossTabs(store, VISITOR, undefined, () => 2_000)).resolves.toBe(2);
        await expect(claimFirstSignupClickAcrossTabs(store, VISITOR, undefined, () => 3_000)).resolves.toBeNull();
    });
});
