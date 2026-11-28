import { describe, expect, it } from 'vitest';
import { createVisitorId, isVisitorId, readVisitorId, VISITOR_ID_COOKIE } from './visitor-id';

const cookieJar = (values: Record<string, string>) => ({
    get: (name: string) => (name in values ? { value: values[name]! } : undefined),
});

describe('createVisitorId', () => {
    it('creates unique, valid version 4 UUIDs', () => {
        const ids = new Set(Array.from({ length: 100 }, createVisitorId));
        expect(ids.size).toBe(100);
        for (const id of ids) {
            expect(isVisitorId(id)).toBe(true);
        }
    });
});

describe('isVisitorId', () => {
    it.each([undefined, '', 'not-a-uuid', '00000000-0000-1000-8000-000000000000', `${createVisitorId()} `])(
        'rejects %j',
        (value) => {
            expect(isVisitorId(value)).toBe(false);
        },
    );
});

describe('readVisitorId', () => {
    it('returns the stored visitor ID', () => {
        const visitorId = createVisitorId();
        expect(readVisitorId(cookieJar({ [VISITOR_ID_COOKIE]: visitorId }))).toBe(visitorId);
    });

    it('returns null for a missing or tampered cookie', () => {
        expect(readVisitorId(cookieJar({}))).toBeNull();
        expect(readVisitorId(cookieJar({ [VISITOR_ID_COOKIE]: '<script>' }))).toBeNull();
    });
});
