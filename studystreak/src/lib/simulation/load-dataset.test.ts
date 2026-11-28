import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { simulatedDataset } from '@/test/simulated-dataset';
import { loadSimulatedDataset } from './load-dataset';

const directories: string[] = [];

afterEach(async () => {
    await Promise.all(directories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

async function fileWith(contents: string) {
    const directory = await mkdtemp(path.join(tmpdir(), 'studystreak-'));
    directories.push(directory);
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
            JSON.stringify(
                simulatedDataset([
                    { visitorId: 'sim-1', variant: 'control', clickedAfterSeconds: null, signedUp: false },
                ]),
            ),
        );
        const result = await loadSimulatedDataset(filePath);
        expect(result.status === 'loaded' && result.dataset.visitors).toHaveLength(1);
    });
});
