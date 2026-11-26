import { NextResponse, type NextRequest } from 'next/server';
import { createVisitorId, isVisitorId, VISITOR_ID_COOKIE, visitorIdCookieOptions } from '@/lib/visitor-id';

export function proxy(request: NextRequest) {
    if (isVisitorId(request.cookies.get(VISITOR_ID_COOKIE)?.value)) {
        return NextResponse.next();
    }

    const visitorId = createVisitorId();
    // Forward the new ID on the request too, so the first server render already sees it.
    request.cookies.set(VISITOR_ID_COOKIE, visitorId);
    const response = NextResponse.next({ request: { headers: request.headers } });
    response.cookies.set(VISITOR_ID_COOKIE, visitorId, visitorIdCookieOptions(request.nextUrl.protocol === 'https:'));
    return response;
}

export const config = {
    // API routes must reuse an existing identity rather than mint one, so they are excluded.
    matcher: ['/((?!api/|_next/static|_next/image|.*\\..*).*)'],
};
