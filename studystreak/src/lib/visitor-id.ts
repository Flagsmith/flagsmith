export const VISITOR_ID_COOKIE = 'studystreak_visitor_id';

const ONE_YEAR_IN_SECONDS = 60 * 60 * 24 * 365;
const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isVisitorId(value: string | undefined): value is string {
    return value !== undefined && UUID_V4_PATTERN.test(value);
}

export function createVisitorId(): string {
    return crypto.randomUUID();
}

export function readVisitorId(cookies: { get(name: string): { value: string } | undefined }): string | null {
    const value = cookies.get(VISITOR_ID_COOKIE)?.value;
    return isVisitorId(value) ? value : null;
}

export function visitorIdCookieOptions(secure: boolean) {
    return {
        httpOnly: true,
        secure,
        sameSite: 'lax',
        path: '/',
        maxAge: ONE_YEAR_IN_SECONDS,
    } as const;
}
