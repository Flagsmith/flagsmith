import { act, type ReactNode } from 'react';
import { createRoot, type Root } from 'react-dom/client';

export type Rendered = {
    container: HTMLDivElement;
    rerender: (ui: ReactNode) => Promise<void>;
    unmount: () => Promise<void>;
};

export async function render(ui: ReactNode): Promise<Rendered> {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    const container = document.createElement('div');
    document.body.append(container);
    const root: Root = createRoot(container);
    const rerender = (next: ReactNode) => act(async () => root.render(next));
    await rerender(ui);
    return {
        container,
        rerender,
        unmount: async () => {
            await act(async () => root.unmount());
            container.remove();
        },
    };
}
