'use client';

import { createFlagsmithInstance } from '@flagsmith/flagsmith';
import { FlagsmithProvider } from '@flagsmith/flagsmith/react';
import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import { useEffect, useRef, useState, type ReactNode } from 'react';

// The SDK's 10 s default loses events from short visits and it does not flush on page hide (see the
// README). A shorter interval narrows that window.
const EVENT_FLUSH_INTERVAL_MS = 1000;
const EVENTS_API_URL = 'https://events.api.flagsmith.com/';

// The browser build sends requests with XMLHttpRequest, which the browser cancels when the page
// unloads. keepalive lets a flush started on pagehide finish after the page has gone.
export function withKeepaliveForEvents(fetchImpl: typeof fetch): typeof fetch {
    return (input, init) =>
        fetchImpl(input, String(input).startsWith(EVENTS_API_URL) ? { ...init, keepalive: true } : init);
}

type ProvidersProps = {
    environmentKey: string | null;
    visitorId: string | null;
    children: ReactNode;
};

export function Providers({ environmentKey, visitorId, children }: ProvidersProps) {
    if (!environmentKey || !visitorId) {
        return children;
    }
    return (
        <FlagsmithSession environmentKey={environmentKey} visitorId={visitorId}>
            {children}
        </FlagsmithSession>
    );
}

function FlagsmithSession({
    environmentKey,
    visitorId,
    children,
}: ProvidersProps & { environmentKey: string; visitorId: string }) {
    const [flagsmith] = useState(createFlagsmithInstance);
    const initStarted = useRef(false);

    // Initialised in an effect rather than through FlagsmithProvider's options, which would also
    // fetch flags during server rendering. The ref keeps Strict Mode from initialising twice.
    useEffect(() => {
        if (initStarted.current) {
            return;
        }
        initStarted.current = true;
        flagsmith
            .init({
                environmentID: environmentKey,
                identity: visitorId,
                enableEvents: true,
                eventProcessorConfig: { flushInterval: EVENT_FLUSH_INTERVAL_MS },
                fetch: withKeepaliveForEvents((input, init) => fetch(input, init)),
            })
            .catch(() => {
                // The SDK records the failure in its loading state, which the experiment UI reads.
            });
    }, [flagsmith, environmentKey, visitorId]);

    useEffect(() => flushEventsWhenPageIsHidden(flagsmith), [flagsmith]);

    return <FlagsmithProvider flagsmith={flagsmith}>{children}</FlagsmithProvider>;
}

// Best effort: browsers do not guarantee requests made while a page unloads. Flushing an empty buffer
// sends nothing, so overlapping triggers cannot duplicate events.
export function flushEventsWhenPageIsHidden(flagsmith: Pick<IFlagsmith, 'flushEvents'>): () => void {
    const flush = () => void flagsmith.flushEvents();
    const flushIfHidden = () => {
        if (document.visibilityState === 'hidden') {
            flush();
        }
    };
    document.addEventListener('visibilitychange', flushIfHidden);
    window.addEventListener('pagehide', flush);
    return () => {
        document.removeEventListener('visibilitychange', flushIfHidden);
        window.removeEventListener('pagehide', flush);
    };
}
