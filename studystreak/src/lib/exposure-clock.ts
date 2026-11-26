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

export function secondsBetween(startMs: number, endMs: number): number {
    return Math.max(0, Math.round((endMs - startMs) / 100) / 10);
}

// localStorage can be missing or throw (private browsing, storage disabled); fall back to memory so
// tracking still works for the current page.
export function createBrowserStore(storage: () => Storage = () => window.localStorage): KeyValueStore {
    const memory = new Map<string, string>();
    return {
        getItem(key) {
            try {
                return storage().getItem(key);
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
