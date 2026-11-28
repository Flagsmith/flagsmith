export type LimitedBodyResult = { ok: true; text: string } | { ok: false; reason: 'too_large' | 'unreadable' };

/**
 * Reads a request body as UTF-8 text, counting bytes as they arrive and cancelling the stream as soon as the total
 * exceeds maxBytes, so an oversized or unbounded body is never buffered in full.
 */
export async function readLimitedBody(
    body: ReadableStream<Uint8Array> | null,
    maxBytes: number,
): Promise<LimitedBodyResult> {
    if (body === null) {
        return { ok: true, text: '' };
    }
    const reader = body.getReader();
    const decoder = new TextDecoder('utf-8', { fatal: true });
    const chunks: string[] = [];
    let received = 0;
    try {
        for (;;) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            received += value.byteLength;
            if (received > maxBytes) {
                await reader.cancel().catch(() => {});
                return { ok: false, reason: 'too_large' };
            }
            chunks.push(decoder.decode(value, { stream: true }));
        }
        chunks.push(decoder.decode());
    } catch {
        await reader.cancel().catch(() => {});
        return { ok: false, reason: 'unreadable' };
    } finally {
        reader.releaseLock();
    }
    return { ok: true, text: chunks.join('') };
}
