import { createFlagsmithInstance } from '@flagsmith/flagsmith';
import { updateRecord } from './attempt-store.js';

const exposure = '$flag_exposure';
const conversion = 'drill_resolved';
const leaseMs = 10000;

function nextEvent(round) {
    if (!round?.measured) return null;
    if (!round.delivery?.[exposure]) return exposure;
    return round.done && round.answer === 'pool' && !round.delivery?.[conversion] ? conversion : null;
}

// Use the SDK's event schema, authentication and transport. Replay the time of the
// original interaction so a late delivery still belongs to the original experiment.
async function sendEvent(round, name, environmentID, root, feature, identifier) {
    let confirmed = false;
    const client = createFlagsmithInstance();
    await client.init({
        environmentID,
        identity: round.identifier || identifier,
        api: root + '/api/v1/',
        preventFetch: true,
        defaultFlags: { [feature]: { enabled: true, value: round.layout } },
        enableEvents: true,
        eventProcessorConfig: { eventsApiUrl: root + '/api/' },
        fetch: async (url, options) => {
            const batch = JSON.parse(options.body);
            batch.events[0].timestamp = name === exposure ? round.deadline - 60000 : round.finishedAt;
            const response = await fetch(url, { ...options, body: JSON.stringify(batch) });
            if (response.ok) {
                const body = await response.clone().text();
                if (body) {
                    const receipt = JSON.parse(body);
                    confirmed = receipt.accepted === 1 && receipt.rejected?.length === 0;
                } else {
                    confirmed = response.status === 202 || response.status === 204;
                }
            }
            return response;
        },
    });
    try {
        if (name === exposure) {
            client.trackExposureEvent(feature, {
                value: round.variant ?? round.layout,
                metadata: round.experimentId ? { experiment_id: round.experimentId } : null,
            });
        } else {
            client.trackEvent(conversion);
        }
    } finally {
        await client.close(4000);
    }
    return confirmed;
}

export function createEventDelivery({ key, environmentID, root, feature, identifier, onChange }) {
    let busy = false;
    let requested = false;
    let timer;

    function schedule(ms) {
        clearTimeout(timer);
        timer = setTimeout(sync, ms);
    }

    async function drain() {
        while (true) {
            const token = crypto.randomUUID();
            const round = await updateRecord(key, (current) => {
                if (!nextEvent(current) || current.delivery?.until > Date.now()) return current;
                return { ...current, delivery: { ...current.delivery, token, until: Date.now() + leaseMs } };
            });
            const name = nextEvent(round);
            if (!name) {
                if (round) onChange(round);
                return;
            }
            if (round.delivery.token !== token) {
                schedule(Math.max(0, round.delivery.until - Date.now()) + 50);
                return;
            }
            let confirmed = false;
            try {
                confirmed = await sendEvent(round, name, environmentID, root, feature, identifier);
            } catch {
                // The saved event stays pending when the network or SDK is unavailable.
            }
            const updated = await updateRecord(key, (current) => {
                if (current?.delivery?.token !== token) return current;
                const delivery = { ...current.delivery, [name]: confirmed, failed: !confirmed };
                delete delivery.token;
                delete delivery.until;
                return { ...current, delivery };
            });
            if (updated) onChange(updated);
            if (!confirmed) {
                schedule(30000);
                return;
            }
        }
    }

    function sync() {
        if (busy) {
            requested = true;
            return;
        }
        busy = true;
        clearTimeout(timer);
        void drain()
            .catch(() => schedule(30000))
            .finally(() => {
                busy = false;
                if (requested) {
                    requested = false;
                    sync();
                }
            });
    }
    window.addEventListener('online', sync);
    return sync;
}
