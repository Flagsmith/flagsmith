import type { ReactNode } from 'react';
import type { SupplementaryAnalysis } from '@/lib/simulation/analysis';
import {
    formatInterval,
    formatPercent,
    formatPercentagePoints,
    formatSeconds,
    formatSignedPercent,
    VERDICT_TEXT,
} from '@/lib/simulation/format';
import type { ConversionComparison } from '@/lib/stats/conversion';

const VARIANT_NAMES = { control: 'Control (plain button)', social_proof: 'Social proof' } as const;

export function SimulatedDataBanner({ label }: { label: string }) {
    return (
        <div role="note" className="rounded-xl border-2 border-dashed border-amber-500 bg-amber-50 p-5 text-amber-950">
            <p className="text-lg font-bold tracking-wide">{label}</p>
            <p className="mt-2 text-sm">
                Every number on this page comes from the traffic simulator, not from real students. It is a
                supplementary check of our own analysis, not an official Flagsmith result. Official experiment results
                are on the experiment&apos;s page in the Flagsmith dashboard.
            </p>
        </div>
    );
}

function Section({ title, label, children }: { title: string; label: string; children: ReactNode }) {
    return (
        <section aria-label={title} className="rounded-xl border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold tracking-wide text-amber-800">{label}</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-900">{title}</h2>
            <div className="mt-4">{children}</div>
        </section>
    );
}

function Table({ headings, rows }: { headings: string[]; rows: ReactNode[][] }) {
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-600">
                    <tr>
                        {headings.map((heading) => (
                            <th key={heading} scope="col" className="py-2 pr-4 font-medium">
                                {heading}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-900 tabular-nums">
                    {rows.map((cells, rowIndex) => (
                        <tr key={rowIndex}>
                            {cells.map((cell, cellIndex) =>
                                cellIndex === 0 ? (
                                    <th key={cellIndex} scope="row" className="py-2 pr-4 font-medium">
                                        {cell}
                                    </th>
                                ) : (
                                    <td key={cellIndex} className="py-2 pr-4">
                                        {cell}
                                    </td>
                                ),
                            )}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function ConversionSection({
    title,
    label,
    comparison,
}: {
    title: string;
    label: string;
    comparison: ConversionComparison;
}) {
    const arms = [
        ['control', comparison.control],
        ['social_proof', comparison.treatment],
    ] as const;
    return (
        <Section title={title} label={label}>
            <Table
                headings={['Variant', 'Visitors', 'Conversions', 'Rate', '95% credible interval']}
                rows={arms.map(([variant, arm]) => [
                    VARIANT_NAMES[variant],
                    arm.visitors,
                    arm.conversions,
                    formatPercent(arm.observedRate),
                    formatInterval(arm.credibleInterval, formatPercent),
                ])}
            />
            <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-3">
                <div>
                    <dt className="text-slate-600">Absolute difference</dt>
                    <dd className="font-semibold text-slate-900">
                        {formatPercentagePoints(comparison.observedAbsoluteDifference)}
                    </dd>
                    <dd className="text-slate-600">
                        95% CrI {formatInterval(comparison.absoluteDifference.credibleInterval, formatPercentagePoints)}
                    </dd>
                </div>
                <div>
                    <dt className="text-slate-600">Relative lift</dt>
                    <dd className="font-semibold text-slate-900">
                        {formatSignedPercent(comparison.observedRelativeLift)}
                    </dd>
                    <dd className="text-slate-600">
                        95% CrI {formatInterval(comparison.relativeLift.credibleInterval, formatSignedPercent)}
                    </dd>
                </div>
                <div>
                    <dt className="text-slate-600">Probability social proof beats control</dt>
                    <dd className="font-semibold text-slate-900">
                        {formatPercent(comparison.probabilityTreatmentBeatsControl)}
                    </dd>
                    <dd className="text-slate-600">{VERDICT_TEXT[comparison.verdict]}</dd>
                </div>
            </dl>
        </Section>
    );
}

export function SupplementaryReport({ analysis }: { analysis: SupplementaryAnalysis }) {
    const { sampleRatio, timeToClick, label } = analysis;
    return (
        <div className="space-y-6">
            <SimulatedDataBanner label={label} />
            <p className="text-sm text-slate-600">
                {analysis.totalVisitors} simulated visitors · seed {analysis.seed} · generated{' '}
                <time dateTime={analysis.generatedAt}>{analysis.generatedAt}</time> · Beta(1, 1) prior, 95% credible
                intervals
            </p>

            <Section title="About this simulated run" label={label}>
                <p className="text-sm text-slate-700">{analysis.disclosure}</p>
                <p className="mt-2 text-sm text-slate-700">
                    Variants were assigned by Flagsmith&apos;s &ldquo;{analysis.run.environmentName}&rdquo; environment.
                    The simulator was set to signup rates of {formatPercent(analysis.run.signupRate.control)} for
                    control and {formatPercent(analysis.run.signupRate.social_proof)} for social proof; these are
                    inputs, not findings. {analysis.run.notEnrolled} visitors were outside the experiment and{' '}
                    {analysis.run.assignmentFailures} could not be assigned.
                </p>
                <Table
                    headings={['Event', 'Sent to the SDK', 'Confirmed by Flagsmith']}
                    rows={Object.entries(analysis.run.eventDelivery).map(([event, { tracked, confirmed }]) => [
                        event,
                        tracked,
                        confirmed,
                    ])}
                />
            </Section>

            <ConversionSection title="Signup completion (signed_up)" label={label} comparison={analysis.signedUp} />
            <ConversionSection
                title="Signup click-through (signup_clicked)"
                label={label}
                comparison={analysis.clickedSignUp}
            />

            <Section title="Sample ratio check (expected 50/50)" label={label}>
                {sampleRatio.status === 'not_checked' ? (
                    <p className="text-sm text-slate-700">
                        Not checked: {sampleRatio.reason} Control {sampleRatio.control}, social proof{' '}
                        {sampleRatio.treatment}.
                    </p>
                ) : (
                    <>
                        <Table
                            headings={['Variant', 'Visitors', 'Expected']}
                            rows={[
                                [VARIANT_NAMES.control, sampleRatio.control, sampleRatio.expectedControl],
                                [VARIANT_NAMES.social_proof, sampleRatio.treatment, sampleRatio.expectedTreatment],
                            ]}
                        />
                        <p className="mt-4 text-sm text-slate-700">
                            <strong className={sampleRatio.status === 'mismatch' ? 'text-red-700' : 'text-slate-900'}>
                                {sampleRatio.status === 'mismatch'
                                    ? 'SRM warning'
                                    : 'No sample ratio mismatch detected'}
                            </strong>{' '}
                            (chi-square {sampleRatio.chiSquare.toFixed(2)}, p = {sampleRatio.pValue.toPrecision(3)};
                            warning below p = 0.001). A passing check cannot prove assignment is correct.
                        </p>
                    </>
                )}
            </Section>

            <Section title="Time to signup click, clickers only" label={label}>
                <Table
                    headings={['Variant', 'Visitors', 'Clickers', 'Mean (clickers)', 'Median (clickers)']}
                    rows={(['control', 'social_proof'] as const).map((variant) => [
                        VARIANT_NAMES[variant],
                        timeToClick[variant].visitors,
                        timeToClick[variant].clickers,
                        formatSeconds(timeToClick[variant].clickerMean),
                        formatSeconds(timeToClick[variant].clickerMedian),
                    ])}
                />
                <p className="mt-4 text-sm text-slate-700">
                    Flagsmith&apos;s official &ldquo;Time to signup click (non-clickers count as 0s)&rdquo; metric is
                    Informational and averages over every exposed visitor, so non-clickers pull it towards zero. On this
                    simulated data it would read {formatSeconds(timeToClick.control.zeroFilledMean)} for control and{' '}
                    {formatSeconds(timeToClick.social_proof.zeroFilledMean)} for social proof.
                </p>
            </Section>
        </div>
    );
}
