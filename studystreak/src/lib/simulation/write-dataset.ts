import { constants } from 'node:fs';
import { copyFile, mkdir, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { parseSimulatedDataset, type SimulatedDataset } from './dataset';

/**
 * Validates the dataset, backs up any existing file, then swaps the new file in with an atomic rename,
 * so a crash never leaves a half-written dataset. Returns the backup path, if one was made.
 */
export async function writeDatasetSafely(
    dataset: SimulatedDataset,
    targetPath: string,
    now: () => Date = () => new Date(),
): Promise<{ backupPath: string | null }> {
    parseSimulatedDataset(JSON.parse(JSON.stringify(dataset)));
    await mkdir(path.dirname(targetPath), { recursive: true });

    const stamp = now().toISOString().replace(/[:.]/g, '-');
    const temporaryPath = `${targetPath}.${stamp}.tmp`;
    await writeFile(temporaryPath, `${JSON.stringify(dataset, null, 2)}\n`, { flag: 'wx' });

    try {
        const backupPath = await backUp(targetPath, stamp);
        await rename(temporaryPath, targetPath);
        return { backupPath };
    } finally {
        await rm(temporaryPath, { force: true });
    }
}

async function backUp(targetPath: string, stamp: string): Promise<string | null> {
    const backupPath = path.join(
        path.dirname(targetPath),
        `${path.basename(targetPath, '.json')}.backup-${stamp}.json`,
    );
    try {
        await copyFile(targetPath, backupPath, constants.COPYFILE_EXCL);
        return backupPath;
    } catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
            return null;
        }
        throw error;
    }
}
