import { SignupCta } from './SignupCta';

const EXAMPLE_WEEK = [
    { day: 'Mon', studied: true },
    { day: 'Tue', studied: true },
    { day: 'Wed', studied: true },
    { day: 'Thu', studied: true },
    { day: 'Fri', studied: true },
    { day: 'Sat', studied: false },
    { day: 'Sun', studied: false },
];

export function Hero() {
    return (
        <section id="top" className="bg-white">
            <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 sm:py-24 lg:grid-cols-2">
                <div className="text-center sm:text-left">
                    <h1 className="text-4xl font-bold tracking-tight text-balance text-slate-900 sm:text-5xl">
                        Build Better Habits. Achieve More.
                    </h1>
                    <p className="mt-5 max-w-xl text-lg text-slate-600 sm:mx-0 mx-auto">
                        Small daily efforts create big results. StudyStreak helps you plan a short study session each
                        day, check it off when you are done, and keep your streak going.
                    </p>
                    <div className="mt-8">
                        <SignupCta />
                    </div>
                </div>
                <StreakPreview />
            </div>
        </section>
    );
}

function StreakPreview() {
    return (
        <figure className="mx-auto w-full max-w-sm rounded-2xl border border-slate-200 bg-slate-50 p-6">
            <figcaption className="text-sm font-semibold text-slate-900">
                Example week <span className="font-normal text-slate-500">· illustration</span>
            </figcaption>
            <ol className="mt-5 grid grid-cols-7 gap-2" aria-label="Five of seven days studied">
                {EXAMPLE_WEEK.map(({ day, studied }) => (
                    <li key={day} className="flex flex-col items-center gap-2">
                        <span
                            aria-hidden="true"
                            className={`grid size-9 place-items-center rounded-full text-sm font-semibold ${
                                studied
                                    ? 'bg-indigo-600 text-white'
                                    : 'border border-dashed border-slate-300 text-slate-400'
                            }`}
                        >
                            {studied ? '✓' : ''}
                        </span>
                        <span className="text-xs text-slate-500">
                            {day}
                            {/* The circle is decorative; this gives each day's status to assistive technology. */}
                            <span className="sr-only">{studied ? ', studied' : ', not studied'}</span>
                        </span>
                    </li>
                ))}
            </ol>
            <p className="mt-5 text-sm text-slate-600">
                <span className="font-semibold text-slate-900">5-day streak.</span> Study today to keep it going.
            </p>
        </figure>
    );
}
