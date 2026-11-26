import { NextResponse, type NextRequest } from 'next/server';
import { readFlagsmithServerConfig } from '@/lib/env';
import { recordSignupConversion } from '@/lib/server/record-signup-conversion';
import { validateSignup } from '@/lib/signup';
import { readVisitorId } from '@/lib/visitor-id';

export type SignupResponse = { status: 'accepted' } | { error: string; fieldErrors?: Record<string, string> };

const respond = (body: SignupResponse, status: number) => NextResponse.json(body, { status });

// The demo validates the signup and records the conversion; the name and email are never stored
// or forwarded.
export async function POST(request: NextRequest) {
    if (!request.headers.get('content-type')?.startsWith('application/json')) {
        return respond({ error: 'Send the sign-up as JSON.' }, 415);
    }

    // The identity always comes from the HTTP-only cookie, never from the request body.
    const visitorId = readVisitorId(request.cookies);
    if (!visitorId) {
        return respond({ error: 'Reload the page and try again.' }, 400);
    }

    let body: unknown;
    try {
        body = await request.json();
    } catch {
        return respond({ error: 'The sign-up request could not be read.' }, 400);
    }
    const signup = validateSignup(body);
    if (!signup.ok) {
        return respond({ error: 'Check the highlighted fields.', fieldErrors: signup.errors }, 422);
    }

    const config = readFlagsmithServerConfig();
    if (!config.ok) {
        console.error(`Sign-up conversions are disabled: ${config.reason}`);
        return respond({ error: 'Sign-up is temporarily unavailable.' }, 503);
    }

    if (!(await recordSignupConversion(visitorId, config.serverKey))) {
        return respond({ error: 'We could not complete your sign-up. Please try again.' }, 502);
    }
    return respond({ status: 'accepted' }, 201);
}
