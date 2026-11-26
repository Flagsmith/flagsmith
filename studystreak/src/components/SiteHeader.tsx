export function SiteHeader() {
    return (
        <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
                <a href="#top" className="flex items-center gap-2 text-lg font-bold text-slate-900">
                    <span
                        aria-hidden="true"
                        className="grid size-8 place-items-center rounded-lg bg-indigo-600 text-white"
                    >
                        S
                    </span>
                    StudyStreak
                </a>
                <nav aria-label="Main">
                    <ul className="flex gap-6 text-sm font-medium text-slate-600">
                        <li>
                            <a href="#features" className="hover:text-slate-900">
                                Features
                            </a>
                        </li>
                        <li>
                            <a href="#how-it-works" className="hover:text-slate-900">
                                How it works
                            </a>
                        </li>
                    </ul>
                </nav>
            </div>
        </header>
    );
}
