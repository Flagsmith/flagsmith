import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { parseSimulatedDataset, type SimulatedDataset } from './dataset';

export const SIMULATED_DATASET_PATH = path.join('simulation', 'simulated-visitors.json');

export type DatasetLoadResult =
    | { status: 'loaded'; dataset: SimulatedDataset }
    | { status: 'missing'; path: string }
    | { status: 'invalid'; path: string; message: string };

export async function loadSimulatedDataset(
    filePath = path.join(process.cwd(), SIMULATED_DATASET_PATH),
): Promise<DatasetLoadResult> {
    let text: string;
    try {
        // Bundled via outputFileTracingIncludes; tracing this dynamic path would add the whole project.
        text = await readFile(/*turbopackIgnore: true*/ filePath, 'utf8');
    } catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
            return { status: 'missing', path: filePath };
        }
        throw error;
    }
    try {
        return { status: 'loaded', dataset: parseSimulatedDataset(JSON.parse(text)) };
    } catch (error) {
        if (error instanceof InvalidDataError || error instanceof SyntaxError) {
            return { status: 'invalid', path: filePath, message: error.message };
        }
        throw error;
    }
}
