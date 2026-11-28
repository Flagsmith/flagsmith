import { NextRequest } from 'next/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { recordSignupConversion } from '@/lib/server/record-signup-conversion';
import { VISITOR_ID_COOKIE } from '@/lib/visitor-id';
import { POST } from './route';

vi.mock('@/lib/server/record-signup-conversion', () => ({ recordSignupConversion: vi.fn() }));

const VISITOR_ID = '6f1c3c1e-5b7a-4d2e-9f8a-3c2b1a0d9e8f';
const VALID_SIGNUP = { name: 'Asha', email: 'asha@example.com' };
const recordConversion = vi.mocked(recordSignupConversion);

function signupRequest({
    body = JSON.stringify(VALID_SIGNUP),
    cookie = `${VISITOR_ID_COOKIE}=${VISITOR_ID}`,
    contentType = 'application/json',
    contentLength,
}: { body?: string; cookie?: string | null; contentType?: string; contentLength?: string } = {}) {
    const headers: Record<string, string> = { 'content-type': contentType };
    if (contentLength) {
        headers['content-length'] = contentLength;
    }
    if (cookie) {
        headers.cookie = cookie;
    }
    return new NextRequest('https://studystreak.test/api/signup', { method: 'POST', headers, body });
}

beforeEach(() => {
    vi.stubEnv('FLAGSMITH_SERVER_KEY', 'ser.production');
    recordConversion.mockReset().mockResolvedValue(true);
    vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
    vi.unstubAllEnvs();
});

describe('POST /api/signup', () => {
    it('accepts a valid signup and records the conversion for the cookie identity', async () => {
        // Given / When
        const response = await POST(signupRequest());

        // Then
        expect(response.status).toBe(201);
        expect(await response.json()).toEqual({ status: 'accepted' });
        expect(recordConversion).toHaveBeenCalledExactlyOnceWith(VISITOR_ID, 'ser.production');
    });

    it('ignores any visitor ID supplied in the body', async () => {
        // Given / When
        await POST(signupRequest({ body: JSON.stringify({ ...VALID_SIGNUP, visitorId: 'someone-else' }) }));

        // Then
        expect(recordConversion).toHaveBeenCalledExactlyOnceWith(VISITOR_ID, 'ser.production');
    });

    it.each([
        ['no visitor cookie', { cookie: null }, 400],
        ['a tampered visitor cookie', { cookie: `${VISITOR_ID_COOKIE}=not-a-uuid` }, 400],
        ['a non-JSON content type', { contentType: 'application/x-www-form-urlencoded' }, 415],
        ['a malformed body', { body: '{"name":' }, 400],
    ])('rejects %s without recording a conversion', async (_case, request, status) => {
        // Given / When
        const response = await POST(signupRequest(request));

        // Then
        expect(response.status).toBe(status);
        expect(recordConversion).not.toHaveBeenCalled();
    });

    it.each([
        ['an oversized body', { body: JSON.stringify({ ...VALID_SIGNUP, padding: 'x'.repeat(4096) }) }],
        ['a declared oversized body', { body: JSON.stringify(VALID_SIGNUP), contentLength: '999999' }],
    ])('rejects %s without reading it into a signup', async (_case, request) => {
        // Given / When
        const response = await POST(signupRequest(request));

        // Then
        expect(response.status).toBe(413);
        expect(recordConversion).not.toHaveBeenCalled();
    });

    it('rejects a streamed oversized body that declares no length, without buffering all of it', async () => {
        // Given: a chunked body with no Content-Length that would never end on its own
        let chunksRead = 0;
        const endless = new ReadableStream<Uint8Array>({
            pull(controller) {
                chunksRead++;
                controller.enqueue(new TextEncoder().encode('x'.repeat(512)));
            },
        });
        const request = new NextRequest('https://studystreak.test/api/signup', {
            method: 'POST',
            headers: { 'content-type': 'application/json', cookie: `${VISITOR_ID_COOKIE}=${VISITOR_ID}` },
            body: endless,
            duplex: 'half',
        } as RequestInit & { duplex: 'half' });

        // When
        const response = await POST(request);

        // Then
        expect(response.status).toBe(413);
        expect(chunksRead).toBeLessThanOrEqual(6);
        expect(recordConversion).not.toHaveBeenCalled();
    });

    it('returns field errors for invalid input without recording a conversion', async () => {
        // Given / When
        const response = await POST(signupRequest({ body: JSON.stringify({ name: '', email: 'nope' }) }));

        // Then
        expect(response.status).toBe(422);
        expect(await response.json()).toMatchObject({
            fieldErrors: { name: expect.any(String), email: expect.any(String) },
        });
        expect(recordConversion).not.toHaveBeenCalled();
    });

    it('refuses to accept signups when the Production server key is missing', async () => {
        // Given
        vi.stubEnv('FLAGSMITH_SERVER_KEY', '');
        vi.stubEnv('FLAGSMITH_SIMULATION_SERVER_KEY', 'ser.simulation');

        // When
        const response = await POST(signupRequest());

        // Then
        expect(response.status).toBe(503);
        expect(recordConversion).not.toHaveBeenCalled();
    });

    it('does not report success when the conversion could not be delivered', async () => {
        // Given
        recordConversion.mockResolvedValue(false);

        // When
        const response = await POST(signupRequest());

        // Then
        expect(response.status).toBe(502);
        expect(await response.json()).toMatchObject({ error: expect.any(String) });
    });

    it('returns a generic error, without logging personal data, when recording throws', async () => {
        // Given
        recordConversion.mockRejectedValue(new Error('events API unreachable'));

        // When
        const response = await POST(signupRequest());

        // Then
        expect(response.status).toBe(502);
        expect(await response.json()).toEqual({ error: 'We could not complete your sign-up. Please try again.' });
        expect(JSON.stringify(vi.mocked(console.error).mock.calls)).not.toMatch(/Asha|asha@example\.com/);
    });
});
