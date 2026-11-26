import type { Metadata } from 'next';
import { SimulatedDataBanner, SupplementaryReport } from '@/components/SupplementaryReport';
import { analyseSimulatedDataset, SIMULATED_DATA_LABEL } from '@/lib/simulation/analysis';
import { loadSimulatedDataset } from '@/lib/simulation/load-dataset';

export const metadata: Metadata = {
    title: 'Simulated data, supplementary analysis · StudyStreak',
    robots: { index: false, follow: false },
};

export const dynamic = 'force-dynamic';

export default async function SupplementaryAnalysisPage() {
    const result = await loadSimulatedDataset();

    return (
        <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Supplementary experiment analysis</h1>
            {result.status === 'loaded' ? (
                <SupplementaryReport analysis={analyseSimulatedDataset(result.dataset)} />
            ) : (
                <>
                    <SimulatedDataBanner label={SIMULATED_DATA_LABEL} />
                    <p role="status" className="rounded-xl border border-slate-200 bg-white p-6 text-slate-700">
                        {result.status === 'missing'
                            ? 'No simulated dataset yet. Run the traffic simulator to generate one.'
                            : `The simulated dataset is invalid and was not analysed: ${result.message}`}
                    </p>
                </>
            )}
        </main>
    );
}
