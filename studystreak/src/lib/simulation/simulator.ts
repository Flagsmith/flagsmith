import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { SIGNED_UP_EVENT, SIGNUP_CLICKED_EVENT, SOCIAL_PROOF_FLAG } from '@/lib/experiment';
import { simulateBehaviour, simulatedVisitorId } from './behaviour';
import { assertSimulationEnvironmentName } from './credentials';
import {
    parseSimulatedDataset,
    SIMULATED_DISCLOSURE,
    TRACKED_EVENTS,
    VARIANTS,
    type SimulatedDataset,
    type SimulatedVisitor,
    type TrackedEvent,
    type Variant,
} from './dataset';
import type { SimulationOptions } from './options';

/** The parts of @flagsmith/nodejs's Flagsmith client the simulator uses. */
export type SimulationClient = {
    getEnvironment(): Promise<{ name: string }>;
    getExperimentFlag(
        featureName: string,
        identifier: string,
    ): Promise<{ enabled: boolean; variant?: string; experiment?: { inExperiment: boolean } }>;
    trackEvent(event: string, opts: { identifier: string; value?: number }): void;
    flushEvents(): Promise<void>;
    close(timeoutMs?: number): Promise<void>;
};

export type SimulationProgress = { completed: number; total: number };

export type SimulationResult = { dataset: SimulatedDataset; failedEventAttempts: number };

export class SimulationSetupError extends Error {
    override name = 'SimulationSetupError';
}

/** Flush every so often so the SDK's buffer (1,000 events by default) never overflows and drops events. */
const FLUSH_EVERY_VISITORS = 50;
const CONCURRENT_ASSIGNMENTS = 4;
/** Stops the run rather than produce a dataset with large gaps. */
const MAX_ASSIGNMENT_FAILURE_SHARE = 0.05;
const CLOSE_TIMEOUT_MS = 30_000;

type Assignment = { status: 'assigned'; variant: Variant } | { status: 'not_enrolled' } | { status: 'failed' };

async function assign(client: SimulationClient, visitorId: string): Promise<Assignment> {
    let flag: Awaited<ReturnType<SimulationClient['getExperimentFlag']>>;
    try {
        flag = await client.getExperimentFlag(SOCIAL_PROOF_FLAG, visitorId);
    } catch {
        return { status: 'failed' };
    }
    if (!flag.enabled) {
        throw new SimulationSetupError(`"${SOCIAL_PROOF_FLAG}" is missing or disabled in the Simulation environment.`);
    }
    if (!flag.experiment) {
        throw new SimulationSetupError(
            `No experiment is running on "${SOCIAL_PROOF_FLAG}" in the Simulation environment.`,
        );
    }
    if (!flag.experiment.inExperiment) {
        return { status: 'not_enrolled' };
    }
    if (!VARIANTS.includes(flag.variant as Variant)) {
        throw new SimulationSetupError(
            `Flagsmith returned the variant "${flag.variant}", but the experiment expects ${VARIANTS.join(' and ')}.`,
        );
    }
    return { status: 'assigned', variant: flag.variant as Variant };
}

/**
 * Runs simulated visitors through the Simulation environment. Flagsmith assigns every variant and records
 * every exposure (getExperimentFlag); the simulator only decides each visitor's clicks and signups.
 */
export async function runSimulation(
    client: SimulationClient,
    options: SimulationOptions,
    {
        confirmedEvents,
        failedEventAttempts,
        onProgress,
        now = () => new Date(),
    }: {
        confirmedEvents: () => Record<TrackedEvent, number>;
        failedEventAttempts: () => number;
        onProgress?: (progress: SimulationProgress) => void;
        now?: () => Date;
    },
): Promise<SimulationResult> {
    const environment = await client.getEnvironment().catch((error: unknown) => {
        throw new SimulationSetupError(
            `Could not read the Simulation environment. Check the key and network access. (${error instanceof Error ? error.message : error})`,
        );
    });
    try {
        assertSimulationEnvironmentName(environment.name);
    } catch (error) {
        throw new SimulationSetupError((error as InvalidDataError).message);
    }

    const tracked = Object.fromEntries(TRACKED_EVENTS.map((event) => [event, 0])) as Record<TrackedEvent, number>;
    const visitors: Array<SimulatedVisitor | null> = new Array(options.visitors).fill(null);
    let notEnrolled = 0;
    let assignmentFailures = 0;

    try {
        for (let start = 0; start < options.visitors; start += FLUSH_EVERY_VISITORS) {
            const indexes = Array.from(
                { length: Math.min(FLUSH_EVERY_VISITORS, options.visitors - start) },
                (_, offset) => start + offset,
            );
            for (let chunk = 0; chunk < indexes.length; chunk += CONCURRENT_ASSIGNMENTS) {
                const batch = indexes.slice(chunk, chunk + CONCURRENT_ASSIGNMENTS);
                const assignments = await Promise.all(
                    batch.map((index) => assign(client, simulatedVisitorId(options.seed, index))),
                );
                assignments.forEach((assignment, position) => {
                    const index = batch[position]!;
                    const visitorId = simulatedVisitorId(options.seed, index);
                    if (assignment.status === 'failed') {
                        assignmentFailures++;
                        return;
                    }
                    if (assignment.status === 'not_enrolled') {
                        notEnrolled++;
                        return;
                    }
                    tracked.$flag_exposure++;
                    const behaviour = simulateBehaviour(options.seed, index, assignment.variant, options);
                    if (behaviour.clickedAfterSeconds !== null) {
                        client.trackEvent(SIGNUP_CLICKED_EVENT, {
                            identifier: visitorId,
                            value: behaviour.clickedAfterSeconds,
                        });
                        tracked.signup_clicked++;
                    }
                    if (behaviour.signedUp) {
                        client.trackEvent(SIGNED_UP_EVENT, { identifier: visitorId });
                        tracked.signed_up++;
                    }
                    visitors[index] = { visitorId, variant: assignment.variant, ...behaviour };
                });
            }
            if (assignmentFailures > options.visitors * MAX_ASSIGNMENT_FAILURE_SHARE) {
                throw new SimulationSetupError(
                    `${assignmentFailures} assignment requests failed. Stopping instead of writing an incomplete dataset.`,
                );
            }
            await client.flushEvents();
            onProgress?.({ completed: indexes.at(-1)! + 1, total: options.visitors });
        }
    } finally {
        await client.close(CLOSE_TIMEOUT_MS);
    }

    const confirmed = confirmedEvents();
    const dataset = parseSimulatedDataset({
        kind: 'simulated',
        environment: 'simulation',
        disclosure: SIMULATED_DISCLOSURE,
        seed: options.seed,
        generatedAt: now().toISOString(),
        run: {
            environmentName: environment.name,
            featureName: SOCIAL_PROOF_FLAG,
            visitorsRequested: options.visitors,
            signupRate: options.signupRate,
            clickToSignupRate: options.clickToSignupRate,
            medianClickSeconds: options.medianClickSeconds,
            notEnrolled,
            assignmentFailures,
            eventDelivery: Object.fromEntries(
                TRACKED_EVENTS.map((event) => [event, { tracked: tracked[event], confirmed: confirmed[event] }]),
            ),
        },
        visitors: visitors.filter((visitor): visitor is SimulatedVisitor => visitor !== null),
    });
    return { dataset, failedEventAttempts: failedEventAttempts() };
}
