import path from 'node:path';
import { Flagsmith } from '@flagsmith/nodejs';
import { analyseSimulatedDataset } from '@/lib/simulation/analysis';
import { readSimulationServerKey } from '@/lib/simulation/credentials';
import { createDeliveryTracker } from '@/lib/simulation/event-delivery';
import { SIMULATED_DATASET_PATH } from '@/lib/simulation/load-dataset';
import { parseSimulationOptions } from '@/lib/simulation/options';
import { runSimulation, SimulationSetupError } from '@/lib/simulation/simulator';
import { writeDatasetSafely } from '@/lib/simulation/write-dataset';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';

const BANNER = '=== SIMULATED TRAFFIC: Flagsmith Simulation environment only ===';

async function main() {
    const options = parseSimulationOptions(process.argv.slice(2));
    const serverKey = readSimulationServerKey(process.env);
    const outputPath = path.join(process.cwd(), SIMULATED_DATASET_PATH);
    const delivery = createDeliveryTracker();
    const flagsmith = new Flagsmith({ environmentKey: serverKey, enableEvents: true, fetch: delivery.fetch });

    console.log(BANNER);
    console.log(
        `Visitors ${options.visitors}, seed ${options.seed}, signup rates: control ${options.signupRate.control}, social proof ${options.signupRate.social_proof}.`,
    );

    const { dataset, failedEventAttempts } = await runSimulation(flagsmith, options, {
        confirmedEvents: delivery.confirmed,
        failedEventAttempts: delivery.failedAttempts,
        onProgress: ({ completed, total }) => console.log(`  ${completed}/${total} simulated visitors`),
    });
    const { backupPath } = await writeDatasetSafely(dataset, outputPath);

    const { run, visitors } = dataset;
    const count = (variant: string) => visitors.filter((visitor) => visitor.variant === variant).length;
    const analysis = analyseSimulatedDataset(dataset);
    console.log(
        [
            '',
            `Environment: ${run.environmentName}`,
            `Assigned by Flagsmith: control ${count('control')}, social proof ${count('social_proof')} (not enrolled ${run.notEnrolled}, assignment failures ${run.assignmentFailures})`,
            `Clicks: control ${analysis.clickedSignUp.control.conversions}, social proof ${analysis.clickedSignUp.treatment.conversions}`,
            `Signups: control ${analysis.signedUp.control.conversions}, social proof ${analysis.signedUp.treatment.conversions}`,
            'Event delivery (confirmed = acknowledged by the events API with a 2xx response):',
            ...Object.entries(run.eventDelivery).map(
                ([event, { tracked, confirmed }]) =>
                    `  ${event}: ${confirmed}/${tracked} confirmed${confirmed < tracked ? ` (${tracked - confirmed} NOT confirmed)` : ''}`,
            ),
            `Failed batch attempts (retried by the SDK where possible): ${failedEventAttempts}`,
            `Dataset written to ${outputPath}${backupPath ? ` (previous dataset backed up to ${backupPath})` : ''}`,
            'Run `npm run analyse:simulation` for the supplementary analysis.',
            BANNER,
        ].join('\n'),
    );
}

main().catch((error: unknown) => {
    if (error instanceof InvalidDataError || error instanceof SimulationSetupError) {
        console.error(`Simulation stopped: ${error.message}`);
    } else {
        console.error('Simulation failed:', error instanceof Error ? error.message : error);
    }
    process.exitCode = 1;
});
