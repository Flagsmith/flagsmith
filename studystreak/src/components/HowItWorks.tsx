const STEPS = [
    { title: 'Sign up', description: 'Join with your name and email in a few seconds.' },
    { title: 'Set a daily goal', description: 'Choose how long you want to study each day.' },
    { title: 'Check in every day', description: 'Mark each session as done and watch your streak grow.' },
];

export function HowItWorks() {
    return (
        <section id="how-it-works" aria-labelledby="how-it-works-heading" className="bg-white py-20">
            <div className="mx-auto max-w-6xl px-6">
                <h2 id="how-it-works-heading" className="text-3xl font-bold tracking-tight text-slate-900">
                    How it works
                </h2>
                <ol className="mt-10 grid gap-8 md:grid-cols-3">
                    {STEPS.map(({ title, description }, index) => (
                        <li key={title} className="flex gap-4">
                            <span
                                aria-hidden="true"
                                className="grid size-9 shrink-0 place-items-center rounded-full bg-slate-900 text-sm font-semibold text-white"
                            >
                                {index + 1}
                            </span>
                            <div>
                                <h3 className="font-semibold text-slate-900">{title}</h3>
                                <p className="mt-1 text-slate-600">{description}</p>
                            </div>
                        </li>
                    ))}
                </ol>
            </div>
        </section>
    );
}
