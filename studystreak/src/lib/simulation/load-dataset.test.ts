import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { loadSimulatedDataset } from './load-dataset';

async function fileWith(contents: string) {
    const directory = await mkdtemp(path.join(tmpdir(), 'studystreak-'));
    const filePath = path.join(directory, 'simulated-visitors.json');
    await writeFile(filePath, contents);
    return filePath;
}

describe('loadSimulatedDataset', () => {
    it('reports a missing file', async () => {
        await expect(loadSimulatedDataset('/nonexistent/simulated-visitors.json')).resolves.toMatchObject({
            status: 'missing',
        });
    });

    it('reports malformed JSON without analysing it', async () => {
        await expect(loadSimulatedDataset(await fileWith('{"kind":'))).resolves.toMatchObject({ status: 'invalid' });
    });

    it('reports a dataset that is not simulated', async () => {
        const filePath = await fileWith(
            JSON.stringify({
                kind: 'real',
                environment: 'production',
                seed: 1,
                generatedAt: '2026-11-26',
                visitors: [],
            }),
        );
        await expect(loadSimulatedDataset(filePath)).resolves.toMatchObject({
            status: 'invalid',
            message: expect.stringContaining('simulated'),
        });
    });

    it('loads a valid dataset', async () => {
        const filePath = await fileWith(
            JSON.stringify({
                kind: 'simulated',
                environment: 'simulation',
                seed: 1,
                generatedAt: '2026-11-26T12:00:00.000Z',
                visitors: [{ visitorId: 'sim-1', variant: 'control', clickedAfterSeconds: null, signedUp: false }],
            }),
        );
        const result = await loadSimulatedDataset(filePath);
        expect(result.status === 'loaded' && result.dataset.visitors).toHaveLength(1);
    });
});
