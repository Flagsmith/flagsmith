// @vitest-environment jsdom
import { act } from 'react';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { installDialogPolyfill } from '@/test/dialog';
import { render, type Rendered } from '@/test/render';
import { SignupDialog } from './SignupDialog';

const fetchMock = vi.fn<typeof fetch>();
const onClose = vi.fn();
let rendered: Rendered;

const query = <T extends Element>(selector: string) => rendered.container.querySelector<T>(selector);
const dialog = () => query<HTMLDialogElement>('dialog')!;
const text = () => dialog().textContent ?? '';

function fillIn(name: string, value: string) {
    const input = query<HTMLInputElement>(`input[name="${name}"]`)!;
    input.value = value;
}

async function submit() {
    await act(async () => {
        query<HTMLFormElement>('form')!.requestSubmit();
    });
}

beforeAll(installDialogPolyfill);

beforeEach(async () => {
    fetchMock.mockReset();
    onClose.mockReset();
    vi.stubGlobal('fetch', fetchMock);
    rendered = await render(<SignupDialog open onClose={onClose} />);
});

afterEach(() => rendered.unmount());

describe('SignupDialog', () => {
    it('opens as a labelled modal that explains the demo', () => {
        expect(dialog().open).toBe(true);
        const title = query(`#${CSS.escape(dialog().getAttribute('aria-labelledby')!)}`);
        expect(title?.textContent).toBe('Sign up for StudyStreak');
        expect(query(`#${CSS.escape(dialog().getAttribute('aria-describedby')!)}`)?.textContent).toContain(
            'No account is created',
        );
    });

    it('shows field errors and sends nothing for invalid input', async () => {
        fillIn('email', 'not-an-email');
        await submit();

        expect(fetchMock).not.toHaveBeenCalled();
        expect(query('input[name="name"]')?.getAttribute('aria-invalid')).toBe('true');
        expect(query('input[name="email"]')?.getAttribute('aria-invalid')).toBe('true');
        expect(text()).toContain('Enter your name.');
        expect(text()).toContain('Enter a valid email address.');
    });

    it('announces client-side field errors and focuses the first invalid field', async () => {
        // Given
        fillIn('name', 'Asha');
        fillIn('email', 'alice@example..com');

        // When
        await submit();

        // Then
        expect(query('[role="alert"]')?.textContent).toBe(
            'Check the highlighted fields. Email: Enter a valid email address.',
        );
        expect(rendered.container.ownerDocument.activeElement).toBe(query('input[name="email"]'));
    });

    it('focuses the name field first when both fields are invalid', async () => {
        // Given / When
        await submit();

        // Then
        expect(query('[role="alert"]')?.textContent).toBe(
            'Check the highlighted fields. Name: Enter your name. Email: Enter your email address.',
        );
        expect(rendered.container.ownerDocument.activeElement).toBe(query('input[name="name"]'));
    });

    it('submits valid input once and shows the success state', async () => {
        fetchMock.mockResolvedValue(Response.json({ status: 'accepted' }, { status: 201 }));
        fillIn('name', ' Asha ');
        fillIn('email', 'asha@example.com');
        await submit();

        expect(fetchMock).toHaveBeenCalledExactlyOnceWith('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'Asha', email: 'asha@example.com' }),
        });
        expect(query('[role="status"]')?.textContent).toContain('Your demo sign-up was received.');
        expect(query('form')).toBeNull();
    });

    it('ignores repeated submits while a request is in flight', async () => {
        let respond: (response: Response) => void = () => {};
        fetchMock.mockReturnValue(new Promise((resolve) => (respond = resolve)));
        fillIn('name', 'Asha');
        fillIn('email', 'asha@example.com');

        await submit();
        expect(query<HTMLButtonElement>('button[type="submit"]')?.disabled).toBe(true);
        expect(query('button[type="submit"]')?.textContent).toBe('Signing up…');
        await act(async () => {
            query<HTMLFormElement>('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        });
        await act(async () => respond(Response.json({ status: 'accepted' }, { status: 201 })));

        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it('shows the server error and keeps the form when the signup fails', async () => {
        fetchMock.mockResolvedValue(
            Response.json({ error: 'We could not complete your sign-up. Please try again.' }, { status: 502 }),
        );
        fillIn('name', 'Asha');
        fillIn('email', 'asha@example.com');
        await submit();

        expect(query('[role="alert"]')?.textContent).toBe('We could not complete your sign-up. Please try again.');
        expect(query('form')).not.toBeNull();
        expect(query<HTMLButtonElement>('button[type="submit"]')?.disabled).toBe(false);
    });

    it('maps server field errors back onto the form', async () => {
        fetchMock.mockResolvedValue(
            Response.json(
                { error: 'Check the highlighted fields.', fieldErrors: { email: 'Enter a valid email address.' } },
                { status: 422 },
            ),
        );
        fillIn('name', 'Asha');
        fillIn('email', 'asha@example.com');
        await submit();

        expect(query('input[name="email"]')?.getAttribute('aria-invalid')).toBe('true');
        expect(query('input[name="name"]')?.getAttribute('aria-invalid')).toBe('false');
    });

    it('reports a network failure', async () => {
        fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));
        fillIn('name', 'Asha');
        fillIn('email', 'asha@example.com');
        await submit();

        expect(query('[role="alert"]')?.textContent).toBe('Check your connection and try again.');
    });

    it('closes from the close button and notifies the parent exactly once', async () => {
        // Given / When
        await act(async () => query<HTMLButtonElement>('button[aria-label="Close"]')!.click());

        // Then
        expect(dialog().open).toBe(false);
        expect(onClose).toHaveBeenCalledOnce();
    });
});
