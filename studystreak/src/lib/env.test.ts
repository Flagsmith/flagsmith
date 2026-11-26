import { describe, expect, it } from 'vitest';
import { readFlagsmithClientConfig } from './env';

describe('readFlagsmithClientConfig', () => {
    it('accepts a client-side environment key', () => {
        expect(readFlagsmithClientConfig({ FLAGSMITH_CLIENT_ENVIRONMENT_KEY: ' abc123 ' })).toEqual({
            ok: true,
            environmentKey: 'abc123',
        });
    });

    it.each([{}, { FLAGSMITH_CLIENT_ENVIRONMENT_KEY: '' }, { FLAGSMITH_CLIENT_ENVIRONMENT_KEY: '   ' }])(
        'reports a missing key for %j',
        (env) => {
            expect(readFlagsmithClientConfig(env)).toMatchObject({ ok: false });
        },
    );

    it('refuses a server-side key so it can never reach the browser', () => {
        const config = readFlagsmithClientConfig({
            FLAGSMITH_CLIENT_ENVIRONMENT_KEY: 'ser.secret',
        });
        expect(config).toMatchObject({ ok: false, reason: expect.stringContaining('server-side key') });
    });
});
