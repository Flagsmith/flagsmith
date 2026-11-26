import { mkdtemp, readdir, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { simulatedDataset, simulatedVisitors } from '@/test/simulated-dataset';
import type { SimulatedDataset } from './dataset';
import { loadSimulatedDataset } from './load-dataset';
import { writeDatasetSafely } from './write-dataset';

const dataset = simulatedDataset(simulatedVisitors('control', 3, 1, 1));
const NOW = () => new Date('2026-11-29T10:00:00.000Z');

async function target() {
    const directory = await mkdtemp(path.join(tmpdir(), 'studystreak-simulation-'));
    return { directory, file: path.join(directory, 'simulated-visitors.json') };
}

describe('writeDatasetSafely', () => {
    it('writes a dataset the loader accepts', async () => {
        const { file } = await target();

        await expect(writeDatasetSafely(dataset, file, NOW)).resolves.toEqual({ backupPath: null });
        await expect(loadSimulatedDataset(file)).resolves.toEqual({ status: 'loaded', dataset });
    });

    it('backs up the previous dataset before replacing it', async () => {
        const { directory, file } = await target();
        await writeFile(file, 'previous run');

        const { backupPath } = await writeDatasetSafely(dataset, file, NOW);

        expect(backupPath).toBe(path.join(directory, 'simulated-visitors.backup-2026-11-29T10-00-00-000Z.json'));
        expect(await readFile(backupPath!, 'utf8')).toBe('previous run');
        expect(JSON.parse(await readFile(file, 'utf8'))).toEqual(dataset);
        expect((await readdir(directory)).filter((name) => name.endsWith('.tmp'))).toEqual([]);
    });

    it('never overwrites an existing backup', async () => {
        const { file } = await target();
        await writeFile(file, 'first');
        await writeDatasetSafely(dataset, file, NOW);

        await expect(writeDatasetSafely(dataset, file, NOW)).rejects.toThrow();
        expect((await readdir(path.dirname(file))).filter((name) => name.endsWith('.tmp'))).toEqual([]);
        expect(JSON.parse(await readFile(file, 'utf8'))).toEqual(dataset);
    });

    it('refuses an invalid dataset and leaves the existing file alone', async () => {
        const { file } = await target();
        await writeFile(file, 'previous run');
        const invalid = { ...dataset, kind: 'real' } as unknown as SimulatedDataset;

        await expect(writeDatasetSafely(invalid, file, NOW)).rejects.toThrow('simulated');
        expect(await readFile(file, 'utf8')).toBe('previous run');
    });
});
