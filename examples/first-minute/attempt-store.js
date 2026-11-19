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

export async function updateRecord(key, change, parseLegacy = JSON.parse) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = database.transaction('rounds', 'readwrite');
        const store = transaction.objectStore('rounds');
        const read = store.get(key);
        let next;
        let failure;
        transaction.oncomplete = () => resolve(next);
        transaction.onabort = () => reject(failure || transaction.error);
        read.onsuccess = () => {
            try {
                next = change(read.result ?? readLegacy(key, parseLegacy));
                if (next !== undefined && next !== read.result) store.put(next, key);
            } catch (error) {
                failure = error;
                transaction.abort();
            }
        };
    });
}
