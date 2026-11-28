const FEATURES = [
    {
        title: 'Build daily study habits',
        description:
            'Set a realistic daily goal, even 20 minutes, so studying becomes a routine instead of a scramble.',
        icon: 'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
    },
    {
        title: 'Track your consistency',
        description: 'Check off each session and see your streak and weekly pattern at a glance.',
        icon: 'M3 3v18h18M7 15l4-4 3 3 5-6',
    },
    {
        title: 'Stay motivated',
        description: 'A visible streak gives you a clear reason to show up again tomorrow.',
        icon: 'M12 2c1 4 5 6 5 11a5 5 0 0 1-10 0c0-2 1-3.5 2-4.5.5 2 1.5 3 3 3 0-3-1-6 0-9.5Z',
    },
];

export function Features() {
    return (
        <section id="features" aria-labelledby="features-heading" className="bg-slate-50 py-20">
            <div className="mx-auto max-w-6xl px-6">
                <h2 id="features-heading" className="text-3xl font-bold tracking-tight text-slate-900">
                    Everything you need to study consistently
                </h2>
                <p className="mt-3 max-w-2xl text-slate-600">
                    StudyStreak keeps things simple: one daily goal, one check-in, and a streak that shows your
                    progress.
                </p>
                <ul className="mt-10 grid gap-6 md:grid-cols-3">
                    {FEATURES.map(({ title, description, icon }) => (
                        <li key={title} className="rounded-2xl border border-slate-200 bg-white p-6">
                            <svg
                                aria-hidden="true"
                                viewBox="0 0 24 24"
                                className="size-10 rounded-lg bg-indigo-50 p-2 text-indigo-600"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth={2}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            >
                                <path d={icon} />
                            </svg>
                            <h3 className="mt-4 text-lg font-semibold text-slate-900">{title}</h3>
                            <p className="mt-2 text-slate-600">{description}</p>
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    );
}
