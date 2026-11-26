'use client';

import { createFlagsmithInstance } from '@flagsmith/flagsmith';
import { FlagsmithProvider } from '@flagsmith/flagsmith/react';
import { useEffect, useRef, useState, type ReactNode } from 'react';

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
        flagsmith.init({ environmentID: environmentKey, identity: visitorId, enableEvents: true }).catch(() => {
            // The SDK records the failure in its loading state, which the experiment UI reads.
        });
    }, [flagsmith, environmentKey, visitorId]);

    return <FlagsmithProvider flagsmith={flagsmith}>{children}</FlagsmithProvider>;
}
