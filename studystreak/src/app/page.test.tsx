// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, type Rendered } from '@/test/render';
import HomePage from './page';

vi.mock('@/lib/use-social-proof-experiment', () => ({
    useSocialProofExperiment: () => ({ status: 'ready', variant: 'control', enrolled: true }),
}));

let rendered: Rendered;

afterEach(() => rendered.unmount());

describe('HomePage', () => {
    it('has one page heading and labelled landmarks', async () => {
        rendered = await render(<HomePage />);
        const { container } = rendered;

        expect([...container.querySelectorAll('h1')].map((heading) => heading.textContent)).toEqual([
            'Build Better Habits. Achieve More.',
        ]);
        expect(container.querySelectorAll('header, main, footer')).toHaveLength(3);
        expect(container.querySelector('nav')?.getAttribute('aria-label')).toBe('Main');
        for (const section of container.querySelectorAll('section[aria-labelledby]')) {
            expect(container.querySelector(`#${section.getAttribute('aria-labelledby')}`)).not.toBeNull();
        }
    });

    it('lists the three features', async () => {
        rendered = await render(<HomePage />);

        const features = [...rendered.container.querySelectorAll('#features h3')].map((heading) => heading.textContent);
        expect(features).toEqual(['Build daily study habits', 'Track your consistency', 'Stay motivated']);
    });

    it('links every in-page navigation target', async () => {
        rendered = await render(<HomePage />);
        const { container } = rendered;

        for (const link of container.querySelectorAll<HTMLAnchorElement>('a[href^="#"]')) {
            expect(container.querySelector(link.getAttribute('href') ?? '')).not.toBeNull();
        }
    });

    it('discloses that the sign-up figure is demonstration content', async () => {
        rendered = await render(<HomePage />);

        expect(rendered.container.querySelector('footer')?.textContent).toContain('demonstration content');
    });
});
