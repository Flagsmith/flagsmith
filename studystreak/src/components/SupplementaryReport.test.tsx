// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { analyseSimulatedDataset } from '@/lib/simulation/analysis';
import type { SimulatedDataset, SimulatedVisitor, Variant } from '@/lib/simulation/dataset';
import { render, type Rendered } from '@/test/render';
import { SupplementaryReport } from './SupplementaryReport';

const LABEL = 'SIMULATED DATA — SUPPLEMENTARY ANALYSIS';

function visitors(variant: Variant, count: number, clicks: number, signups: number): SimulatedVisitor[] {
    return Array.from({ length: count }, (_, index) => ({
        visitorId: `sim-${variant}-${index}`,
        variant,
        clickedAfterSeconds: index < clicks ? 2 + index : null,
        signedUp: index < signups,
    }));
}

const dataset = (controlCount: number, treatmentCount: number): SimulatedDataset => ({
    kind: 'simulated',
    environment: 'simulation',
    seed: 3,
    generatedAt: '2026-11-26T12:00:00.000Z',
    visitors: [...visitors('control', controlCount, 80, 50), ...visitors('social_proof', treatmentCount, 90, 62)],
});

let rendered: Rendered;
afterEach(() => rendered.unmount());

const renderReport = async (data: SimulatedDataset) => {
    rendered = await render(<SupplementaryReport analysis={analyseSimulatedDataset(data)} />);
    return rendered.container;
};

describe('SupplementaryReport', () => {
    it('labels the page and every result section as simulated supplementary analysis', async () => {
        const container = await renderReport(dataset(500, 500));
        const sections = [...container.querySelectorAll('section')];

        expect(container.querySelector('[role="note"]')?.textContent).toContain(LABEL);
        expect(container.querySelector('[role="note"]')?.textContent).toContain('not an official Flagsmith result');
        expect(sections).toHaveLength(4);
        for (const section of sections) {
            expect(section.textContent).toContain(LABEL);
        }
    });

    it('shows sample sizes, rates, lift, intervals and the posterior probability', async () => {
        const text = (await renderReport(dataset(500, 500))).textContent ?? '';

        expect(text).toContain('10.0%');
        expect(text).toContain('12.4%');
        expect(text).toContain('+2.4 pp');
        expect(text).toContain('+24.0%');
        expect(text).toContain('88.5%');
        expect(text).toMatch(/95% CrI/);
        expect(text).toContain('Inconclusive');
    });

    it('reports clicker-only times separately from the official zero-filled metric', async () => {
        const section = [...(await renderReport(dataset(500, 500))).querySelectorAll('section')][3]!;

        expect(section.textContent).toContain('Time to signup click, clickers only');
        expect(section.textContent).toContain('41.5 s');
        expect(section.textContent).toContain('non-clickers count as 0s');
        expect(section.textContent).toContain('Informational');
    });

    it('shows an SRM warning when the split is off', async () => {
        const text = (await renderReport(dataset(560, 440))).textContent ?? '';

        expect(text).toContain('SRM warning');
        expect(text).toContain('A passing check cannot prove assignment is correct');
    });

    it('explains when the SRM check is skipped for a small sample', async () => {
        const small: SimulatedDataset = {
            ...dataset(0, 0),
            visitors: [...visitors('control', 20, 5, 2), ...visitors('social_proof', 20, 6, 3)],
        };
        const text = (await renderReport(small)).textContent ?? '';

        expect(text).toContain('Not checked: Needs at least 100 visitors.');
        expect(text).toContain('Not enough data');
    });
});
