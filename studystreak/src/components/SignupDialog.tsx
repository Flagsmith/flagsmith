'use client';

import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { NAME_MAX_LENGTH, validateSignup, type SignupErrors } from '@/lib/signup';

type SubmissionState =
    | { status: 'editing'; errors: SignupErrors; message?: string }
    | { status: 'submitting' }
    | { status: 'accepted' };

type SignupResponseBody = { error?: string; fieldErrors?: SignupErrors };

const INITIAL_STATE: SubmissionState = { status: 'editing', errors: {} };

async function submitSignup(form: HTMLFormElement): Promise<SubmissionState> {
    const formData = new FormData(form);
    const signup = validateSignup({ name: formData.get('name'), email: formData.get('email') });
    if (!signup.ok) {
        return { status: 'editing', errors: signup.errors };
    }
    try {
        const response = await fetch('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(signup.value),
        });
        if (response.ok) {
            return { status: 'accepted' };
        }
        const body = (await response.json().catch(() => ({}))) as SignupResponseBody;
        return {
            status: 'editing',
            errors: body.fieldErrors ?? {},
            message: body.error ?? 'Something went wrong. Please try again.',
        };
    } catch {
        return { status: 'editing', errors: {}, message: 'Check your connection and try again.' };
    }
}

export function SignupDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const submitting = useRef(false);
    const [state, setState] = useState<SubmissionState>(INITIAL_STATE);
    const ids = { title: useId(), notice: useId(), name: useId(), email: useId() };

    useEffect(() => {
        const dialog = dialogRef.current;
        if (open && !dialog?.open) {
            dialog?.showModal();
        } else if (!open && dialog?.open) {
            dialog.close();
        }
    }, [open]);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (submitting.current) {
            return;
        }
        submitting.current = true;
        setState({ status: 'submitting' });
        setState(await submitSignup(event.currentTarget));
        submitting.current = false;
    }

    const errors = state.status === 'editing' ? state.errors : {};
    const inputClass =
        'mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-600 focus:outline-2 focus:outline-indigo-600 aria-invalid:border-red-600';

    return (
        <dialog
            ref={dialogRef}
            onClose={onClose}
            aria-labelledby={ids.title}
            aria-describedby={ids.notice}
            className="m-auto w-[calc(100%-2rem)] max-w-md rounded-2xl p-0 shadow-xl backdrop:bg-slate-900/50"
        >
            <div className="p-6">
                <div className="flex items-start justify-between gap-4">
                    <h2 id={ids.title} className="text-xl font-semibold text-slate-900">
                        {state.status === 'accepted' ? 'Thanks for signing up' : 'Sign up for StudyStreak'}
                    </h2>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="rounded-md px-2 text-2xl leading-none text-slate-500 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-indigo-600"
                    >
                        ×
                    </button>
                </div>
                <p id={ids.notice} className="mt-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                    This is a demo for a hackathon A/B test. No account is created, and your name and email are not
                    stored.
                </p>

                {state.status === 'accepted' ? (
                    <div role="status" className="mt-5">
                        <p className="text-slate-700">Thanks for trying StudyStreak. Your demo sign-up was received.</p>
                        <button
                            type="button"
                            onClick={onClose}
                            className="mt-5 h-11 w-full rounded-lg bg-indigo-600 font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            Close
                        </button>
                    </div>
                ) : (
                    <form noValidate onSubmit={handleSubmit} className="mt-5 space-y-4">
                        <div>
                            <label htmlFor={ids.name} className="text-sm font-medium text-slate-900">
                                Name
                            </label>
                            <input
                                id={ids.name}
                                name="name"
                                autoComplete="name"
                                maxLength={NAME_MAX_LENGTH}
                                required
                                aria-invalid={Boolean(errors.name)}
                                aria-describedby={errors.name ? `${ids.name}-error` : undefined}
                                className={inputClass}
                            />
                            {errors.name && (
                                <p id={`${ids.name}-error`} className="mt-1 text-sm text-red-700">
                                    {errors.name}
                                </p>
                            )}
                        </div>
                        <div>
                            <label htmlFor={ids.email} className="text-sm font-medium text-slate-900">
                                Email
                            </label>
                            <input
                                id={ids.email}
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                aria-invalid={Boolean(errors.email)}
                                aria-describedby={errors.email ? `${ids.email}-error` : undefined}
                                className={inputClass}
                            />
                            {errors.email && (
                                <p id={`${ids.email}-error`} className="mt-1 text-sm text-red-700">
                                    {errors.email}
                                </p>
                            )}
                        </div>
                        {state.status === 'editing' && state.message && (
                            <p role="alert" className="text-sm text-red-700">
                                {state.message}
                            </p>
                        )}
                        <button
                            type="submit"
                            disabled={state.status === 'submitting'}
                            className="h-11 w-full rounded-lg bg-indigo-600 font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-wait disabled:opacity-70"
                        >
                            {state.status === 'submitting' ? 'Signing up…' : 'Sign up'}
                        </button>
                    </form>
                )}
            </div>
        </dialog>
    );
}
