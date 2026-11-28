import { NextRequest } from 'next/server';
import { describe, expect, it } from 'vitest';
import { createVisitorId, isVisitorId, VISITOR_ID_COOKIE } from '@/lib/visitor-id';
import { proxy } from './proxy';

const requestFor = (url: string, cookie?: string) =>
    new NextRequest(url, { headers: cookie ? { cookie: `${VISITOR_ID_COOKIE}=${cookie}` } : {} });

describe('proxy', () => {
    it('keeps an existing visitor ID without rewriting the cookie', () => {
        const response = proxy(requestFor('https://studystreak.test/', createVisitorId()));
        expect(response.headers.get('set-cookie')).toBeNull();
    });

    it('issues a persistent, HTTP-only cookie to a new visitor', () => {
        const response = proxy(requestFor('https://studystreak.test/'));
        const cookie = response.cookies.get(VISITOR_ID_COOKIE);

        expect(isVisitorId(cookie?.value)).toBe(true);
        expect(cookie).toMatchObject({ httpOnly: true, secure: true, sameSite: 'lax', path: '/', maxAge: 31536000 });
    });

    it('forwards the new ID to the current render so server and browser agree', () => {
        const response = proxy(requestFor('https://studystreak.test/'));
        const issued = response.cookies.get(VISITOR_ID_COOKIE)?.value;

        expect(response.headers.get('x-middleware-request-cookie')).toContain(`${VISITOR_ID_COOKIE}=${issued}`);
    });

    it('replaces a tampered cookie', () => {
        const response = proxy(requestFor('https://studystreak.test/', 'tampered'));
        expect(isVisitorId(response.cookies.get(VISITOR_ID_COOKIE)?.value)).toBe(true);
    });

    it('omits the Secure attribute over plain HTTP for local development', () => {
        const response = proxy(requestFor('http://localhost:3000/'));
        expect(response.cookies.get(VISITOR_ID_COOKIE)?.secure).toBe(false);
    });
});
