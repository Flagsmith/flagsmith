export type KeyValueStore = Pick<Storage, 'getItem' | 'setItem'>;

const firstExposureKey = (visitorId: string) => `studystreak:${visitorId}:first-exposure-ms`;
const signupClickedKey = (visitorId: string) => `studystreak:${visitorId}:signup-clicked`;

// Flagsmith attributes each visitor to their first exposure, so only the first one is kept.
export function recordFirstExposure(store: KeyValueStore, visitorId: string, nowMs = Date.now()): void {
    if (store.getItem(firstExposureKey(visitorId)) === null) {
        store.setItem(firstExposureKey(visitorId), String(nowMs));
    }
}

// Returns the seconds since first exposure for the visitor's first click, or null when the click
// has already been counted or no exposure was recorded.
export function claimFirstSignupClick(store: KeyValueStore, visitorId: string, nowMs = Date.now()): number | null {
    if (store.getItem(signupClickedKey(visitorId)) !== null) {
        return null;
    }
    const storedExposure = store.getItem(firstExposureKey(visitorId));
    const exposedAtMs = Number(storedExposure);
    if (storedExposure === null || !Number.isFinite(exposedAtMs)) {
        return null;
    }
    store.setItem(signupClickedKey(visitorId), '1');
    return secondsBetween(exposedAtMs, nowMs);
}

/** The part of the Web Locks API used to serialise the first-click claim across tabs. */
export type LockManagerLike = Pick<LockManager, 'request'>;

const signupClickLockName = (visitorId: string) => `studystreak:${visitorId}:signup-click-claim`;

/**
 * claimFirstSignupClick, serialised across tabs with an exclusive Web Lock per visitor, so two tabs cannot both read
 * the absent marker before either writes it. Without the Web Locks API it falls back to the unserialised claim.
 */
export async function claimFirstSignupClickAcrossTabs(
    store: KeyValueStore,
    visitorId: string,
    locks: LockManagerLike | undefined = typeof navigator === 'undefined' ? undefined : navigator.locks,
    now: () => number = Date.now,
): Promise<number | null> {
    if (!locks) {
        return claimFirstSignupClick(store, visitorId, now());
    }
    return locks.request(signupClickLockName(visitorId), () => claimFirstSignupClick(store, visitorId, now()));
}

export function secondsBetween(startMs: number, endMs: number): number {
    return Math.max(0, Math.round((endMs - startMs) / 100) / 10);
}

// localStorage can be missing or throw (private browsing, storage disabled, quota exceeded); fall back to memory so
// tracking still works for the current page. A value that could only be written to memory is still found when
// localStorage reads succeed but miss.
export function createBrowserStore(storage: () => Storage = () => window.localStorage): KeyValueStore {
    const memory = new Map<string, string>();
    return {
        getItem(key) {
            try {
                return storage().getItem(key) ?? memory.get(key) ?? null;
            } catch {
                return memory.get(key) ?? null;
            }
        },
        setItem(key, value) {
            try {
                storage().setItem(key, value);
            } catch {
                memory.set(key, value);
            }
        },
    };
}
