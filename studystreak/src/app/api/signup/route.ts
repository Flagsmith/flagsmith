import { NextResponse, type NextRequest } from 'next/server';
import { readFlagsmithServerConfig } from '@/lib/env';
import { readLimitedBody } from '@/lib/server/read-limited-body';
import { recordSignupConversion } from '@/lib/server/record-signup-conversion';
import { validateSignup } from '@/lib/signup';
import { readVisitorId } from '@/lib/visitor-id';

export type SignupResponse = { status: 'accepted' } | { error: string; fieldErrors?: Record<string, string> };

const MAX_BODY_BYTES = 2048;

const respond = (body: SignupResponse, status: number) => NextResponse.json(body, { status });

async function readJsonBody(
    request: NextRequest,
): Promise<{ ok: true; body: unknown } | { ok: false; status: number }> {
    // A declared oversized length is refused without reading; otherwise the limit is enforced while streaming.
    if (Number(request.headers.get('content-length') ?? 0) > MAX_BODY_BYTES) {
        return { ok: false, status: 413 };
    }
    const read = await readLimitedBody(request.body, MAX_BODY_BYTES);
    if (!read.ok) {
        return { ok: false, status: read.reason === 'too_large' ? 413 : 400 };
    }
    try {
        return { ok: true, body: JSON.parse(read.text) };
    } catch {
        return { ok: false, status: 400 };
    }
}

// The demo validates the signup and records the conversion; the name and email are never stored,
// logged or forwarded. Rate limiting belongs at the hosting edge, not in this per-instance handler.
export async function POST(request: NextRequest) {
    if (!request.headers.get('content-type')?.startsWith('application/json')) {
        return respond({ error: 'Send the sign-up as JSON.' }, 415);
    }

    // The identity always comes from the HTTP-only cookie, never from the request body.
    const visitorId = readVisitorId(request.cookies);
    if (!visitorId) {
        return respond({ error: 'Reload the page and try again.' }, 400);
    }

    const body = await readJsonBody(request);
    if (!body.ok) {
        return respond({ error: 'The sign-up request could not be read.' }, body.status);
    }
    const signup = validateSignup(body.body);
    if (!signup.ok) {
        return respond({ error: 'Check the highlighted fields.', fieldErrors: signup.errors }, 422);
    }

    const config = readFlagsmithServerConfig();
    if (!config.ok) {
        console.error(`Sign-up conversions are disabled: ${config.reason}`);
        return respond({ error: 'Sign-up is temporarily unavailable.' }, 503);
    }

    let recorded = false;
    try {
        recorded = await recordSignupConversion(visitorId, config.serverKey);
    } catch (error) {
        console.error('Recording a sign-up conversion failed.', error instanceof Error ? error.message : error);
    }
    if (!recorded) {
        return respond({ error: 'We could not complete your sign-up. Please try again.' }, 502);
    }
    return respond({ status: 'accepted' }, 201);
}
