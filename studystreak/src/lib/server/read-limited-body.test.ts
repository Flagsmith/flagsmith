import { describe, expect, it } from 'vitest';
import { readLimitedBody } from './read-limited-body';

const encoder = new TextEncoder();

function streamOf(chunks: string[]) {
    return new ReadableStream<Uint8Array>({
        start(controller) {
            chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
            controller.close();
        },
    });
}

describe('readLimitedBody', () => {
    it('returns the text of a body within the limit', async () => {
        // Given
        const body = streamOf(['{"name":', '"Asha"}']);

        // When
        const result = await readLimitedBody(body, 2048);

        // Then
        expect(result).toEqual({ ok: true, text: '{"name":"Asha"}' });
    });

    it('accepts a body of exactly the limit', async () => {
        expect(await readLimitedBody(streamOf(['x'.repeat(16)]), 16)).toEqual({ ok: true, text: 'x'.repeat(16) });
    });

    it('counts bytes, not characters', async () => {
        // Given: 6 characters, 12 bytes in UTF-8
        const body = streamOf(['éééééé']);

        // When / Then
        expect(await readLimitedBody(body, 11)).toEqual({ ok: false, reason: 'too_large' });
    });

    it('stops reading an unbounded body as soon as it passes the limit, and cancels the stream', async () => {
        // Given: a stream that never ends on its own
        let pulls = 0;
        let cancelled = false;
        const endless = new ReadableStream<Uint8Array>({
            pull(controller) {
                pulls++;
                controller.enqueue(encoder.encode('x'.repeat(512)));
            },
            cancel() {
                cancelled = true;
            },
        });

        // When
        const result = await readLimitedBody(endless, 2048);

        // Then
        expect(result).toEqual({ ok: false, reason: 'too_large' });
        expect(cancelled).toBe(true);
        expect(pulls).toBeLessThanOrEqual(6);
    });

    it('rejects a body that is not valid UTF-8', async () => {
        // Given
        const invalid = new ReadableStream<Uint8Array>({
            start(controller) {
                controller.enqueue(new Uint8Array([0xff, 0xfe]));
                controller.close();
            },
        });

        // When / Then
        expect(await readLimitedBody(invalid, 2048)).toEqual({ ok: false, reason: 'unreadable' });
    });

    it('treats a missing body as empty', async () => {
        expect(await readLimitedBody(null, 2048)).toEqual({ ok: true, text: '' });
    });
});
