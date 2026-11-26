export type FlagsmithClientConfig = { ok: true; environmentKey: string } | { ok: false; reason: string };

const SERVER_SIDE_KEY_PREFIX = 'ser.';

// Read on the server and passed to the client as a prop, so the key is configured at runtime, not build time.
export function readFlagsmithClientConfig(
    env: Readonly<Record<string, string | undefined>> = process.env,
): FlagsmithClientConfig {
    const environmentKey = env.FLAGSMITH_CLIENT_ENVIRONMENT_KEY?.trim();
    if (!environmentKey) {
        return { ok: false, reason: 'FLAGSMITH_CLIENT_ENVIRONMENT_KEY is not set.' };
    }
    if (environmentKey.startsWith(SERVER_SIDE_KEY_PREFIX)) {
        return {
            ok: false,
            reason: 'FLAGSMITH_CLIENT_ENVIRONMENT_KEY holds a server-side key; use the client-side key instead.',
        };
    }
    return { ok: true, environmentKey };
}
