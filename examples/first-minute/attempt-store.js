// IndexedDB serialises read/write transactions across tabs. A first answer can
// therefore claim the conversion even when two windows submit at the same time.
let connection;
function openDatabase() {
    if (!connection) {
        connection = new Promise((resolve, reject) => {
            const request = indexedDB.open('first-minute', 1);
            request.onupgradeneeded = () => request.result.createObjectStore('rounds');
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    return connection;
}

function readLegacy(key, parse) {
    try {
        const value = localStorage.getItem(key);
        return value === null ? undefined : parse(value);
    } catch {
        return undefined;
    }
}

export function claimAnswer(key, submission) {
    const claim = () =>
        updateRecord(key, (existing) => (existing?.deadline === submission.deadline ? existing : submission));
    if (!navigator.locks) return claim();
    // Serialise the fallback with the database claim if a tab temporarily loses write access.
    return navigator.locks.request(key, async () => {
        try {
            return await claim();
        } catch {
            const existing = readLegacy(key, JSON.parse);
            if (existing?.deadline === submission.deadline) return existing;
            localStorage.setItem(key, JSON.stringify(submission));
            return submission;
        }
    });
}

export function clearPendingAnswer(key) {
    try {
        localStorage.removeItem(key);
    } catch {
        // A completed IndexedDB record takes precedence over a stale journal entry.
    }
}

export async function updateRecord(key, change, { parseLegacy = JSON.parse, relatedKey } = {}) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = database.transaction('rounds', 'readwrite');
        const store = transaction.objectStore('rounds');
        // Both reads see the same state, even if another tab is claiming the desk or an answer.
        const related = relatedKey && store.get(relatedKey);
        const read = store.get(key);
        let next;
        let failure;
        transaction.oncomplete = () => resolve(next);
        transaction.onabort = () => reject(failure || transaction.error);
        read.onsuccess = () => {
            try {
                const relatedRecord = related && (related.result ?? readLegacy(relatedKey, JSON.parse));
                next = change(read.result ?? readLegacy(key, parseLegacy), relatedRecord);
                if (next !== undefined && next !== read.result) store.put(next, key);
            } catch (error) {
                failure = error;
                transaction.abort();
            }
        };
    });
}
