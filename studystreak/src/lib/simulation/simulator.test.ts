import { Flagsmith } from '@flagsmith/nodejs';
import { describe, expect, it, vi } from 'vitest';
import { analyseSimulatedDataset } from './analysis';
import { simulatedVisitorId } from './behaviour';
import { createDeliveryTracker } from './event-delivery';
import { DEFAULT_OPTIONS, type SimulationOptions } from './options';
import { runSimulation, SimulationSetupError, type SimulationClient } from './simulator';

const OPTIONS: SimulationOptions = { ...DEFAULT_OPTIONS, visitors: 120, seed: 5 };
const NOW = () => new Date('2026-11-29T10:00:00.000Z');

// Stands in for Flagsmith's bucketing: deliberately not 50/50, so a hardcoded split would fail.
const flagsmithVariant = (identifier: string) =>
    [...identifier].reduce((sum, char) => sum + char.charCodeAt(0), 0) % 10 < 7 ? 'control' : 'social_proof';

type FakeClientOptions = {
    environmentName?: string;
    flag?: (identifier: string) => Awaited<ReturnType<SimulationClient['getExperimentFlag']>>;
};

function fakeClient({ environmentName = 'Simulation', flag }: FakeClientOptions = {}) {
    const tracked: Array<{ event: string; identifier: string; value?: number }> = [];
    const client = {
        getEnvironment: vi.fn(async () => ({ name: environmentName })),
        getExperimentFlag: vi.fn(async (_feature: string, identifier: string) =>
            flag
                ? flag(identifier)
                : { enabled: true, variant: flagsmithVariant(identifier), experiment: { inExperiment: true } },
        ),
        trackEvent: vi.fn(
            (event: string, opts: { identifier: string; value?: number }) => void tracked.push({ event, ...opts }),
        ),
        flushEvents: vi.fn(async () => {}),
        close: vi.fn(async () => {}),
    };
    return { client, tracked };
}

const callbacks = (confirmed = { $flag_exposure: 0, signup_clicked: 0, signed_up: 0 }) => ({
    confirmedEvents: () => confirmed,
    failedEventAttempts: () => 0,
    now: NOW,
});

describe('runSimulation', () => {
    it('records the variant Flagsmith assigned to each simulated identity', async () => {
        const { client } = fakeClient();
        const { dataset } = await runSimulation(client, OPTIONS, callbacks());

        expect(client.getExperimentFlag).toHaveBeenCalledTimes(120);
        expect(client.getExperimentFlag).toHaveBeenCalledWith('study_streak_social_proof', simulatedVisitorId(5, 0));
        for (const visitor of dataset.visitors) {
            expect(visitor.variant).toBe(flagsmithVariant(visitor.visitorId));
        }
        const controlShare = dataset.visitors.filter((visitor) => visitor.variant === 'control').length / 120;
        expect(controlShare).not.toBeCloseTo(0.5, 1);
    });

    it('sends events with the exact names, the same identity and click times in seconds', async () => {
        const { client, tracked } = fakeClient();
        const { dataset } = await runSimulation(client, OPTIONS, callbacks());

        expect(new Set(tracked.map((event) => event.event))).toEqual(new Set(['signup_clicked', 'signed_up']));
        for (const visitor of dataset.visitors) {
            const events = tracked.filter((event) => event.identifier === visitor.visitorId);
            const click = events.find((event) => event.event === 'signup_clicked');
            expect(click?.value ?? null).toBe(visitor.clickedAfterSeconds);
            expect(events.some((event) => event.event === 'signed_up')).toBe(visitor.signedUp);
        }
        expect(tracked.filter((event) => event.event === 'signed_up').every((event) => event.value === undefined)).toBe(
            true,
        );
    });

    it('writes a valid, labelled dataset with tracked and confirmed event counts', async () => {
        const { client, tracked } = fakeClient();
        const { dataset } = await runSimulation(
            client,
            OPTIONS,
            callbacks({ $flag_exposure: 120, signup_clicked: 3, signed_up: 1 }),
        );

        expect(dataset).toMatchObject({
            kind: 'simulated',
            environment: 'simulation',
            seed: 5,
            generatedAt: NOW().toISOString(),
        });
        expect(dataset.disclosure).toContain('None are real students');
        expect(dataset.visitors).toHaveLength(120);
        expect(dataset.run).toMatchObject({
            environmentName: 'Simulation',
            visitorsRequested: 120,
            notEnrolled: 0,
            assignmentFailures: 0,
        });
        expect(dataset.run.eventDelivery.$flag_exposure).toEqual({ tracked: 120, confirmed: 120 });
        expect(dataset.run.eventDelivery.signup_clicked).toEqual({
            tracked: tracked.filter((event) => event.event === 'signup_clicked').length,
            confirmed: 3,
        });
    });

    it('is reproducible', async () => {
        const first = await runSimulation(fakeClient().client, OPTIONS, callbacks());
        const second = await runSimulation(fakeClient().client, OPTIONS, callbacks());
        expect(second.dataset).toEqual(first.dataset);
    });

    it('flushes regularly and always closes the client', async () => {
        const { client } = fakeClient();
        await runSimulation(client, OPTIONS, callbacks());

        expect(client.flushEvents).toHaveBeenCalledTimes(3);
        expect(client.close).toHaveBeenCalledOnce();
    });

    it.each(['Production', 'Staging'])(
        'refuses the %s environment before sending anything',
        async (environmentName) => {
            const { client } = fakeClient({ environmentName });

            await expect(runSimulation(client, OPTIONS, callbacks())).rejects.toThrow(SimulationSetupError);
            expect(client.getExperimentFlag).not.toHaveBeenCalled();
            expect(client.trackEvent).not.toHaveBeenCalled();
        },
    );

    it('stops when the environment cannot be read', async () => {
        const { client } = fakeClient();
        client.getEnvironment.mockRejectedValue(new Error('401'));

        await expect(runSimulation(client, OPTIONS, callbacks())).rejects.toThrow(
            'Could not read the Simulation environment',
        );
    });

    it.each([
        ['the flag is disabled', { enabled: false }, 'missing or disabled'],
        ['no experiment is running', { enabled: true, variant: 'control' }, 'No experiment is running'],
        [
            'an unexpected variant comes back',
            { enabled: true, variant: 'treatment', experiment: { inExperiment: true } },
            'expects control and social_proof',
        ],
    ])('stops with a setup error when %s', async (_case, flag, message) => {
        const { client } = fakeClient({ flag: () => flag });

        await expect(runSimulation(client, OPTIONS, callbacks())).rejects.toThrow(message);
        expect(client.trackEvent).not.toHaveBeenCalled();
        expect(client.close).toHaveBeenCalledOnce();
    });

    it('leaves out visitors Flagsmith did not enrol, and counts them', async () => {
        const { client, tracked } = fakeClient({
            flag: (identifier) => ({
                enabled: true,
                variant: 'control',
                experiment: { inExperiment: !identifier.endsWith('0') },
            }),
        });
        const { dataset } = await runSimulation(client, OPTIONS, callbacks());

        expect(dataset.run.notEnrolled).toBe(12);
        expect(dataset.visitors).toHaveLength(108);
        expect(tracked.some((event) => event.identifier.endsWith('0'))).toBe(false);
    });

    it('counts occasional assignment failures without inventing a variant', async () => {
        const { client } = fakeClient();
        client.getExperimentFlag.mockImplementation(async (_feature, identifier) => {
            if (identifier.endsWith('00007')) {
                throw new Error('timeout');
            }
            return { enabled: true, variant: flagsmithVariant(identifier), experiment: { inExperiment: true } };
        });
        const { dataset } = await runSimulation(client, OPTIONS, callbacks());

        expect(dataset.run.assignmentFailures).toBe(1);
        expect(dataset.visitors.some((visitor) => visitor.visitorId.endsWith('00007'))).toBe(false);
    });

    it('stops rather than write a dataset with many assignment failures', async () => {
        const { client } = fakeClient();
        client.getExperimentFlag.mockRejectedValue(new Error('timeout'));

        await expect(runSimulation(client, OPTIONS, callbacks())).rejects.toThrow('assignment requests failed');
    });
});

describe('runSimulation with the real Node SDK', () => {
    const environmentDocument = {
        id: 1,
        api_key: 'env',
        name: 'Simulation',
        feature_states: [],
        project: {
            id: 1,
            name: 'StudyStreak',
            hide_disabled_flags: false,
            organisation: {
                id: 1,
                name: 'Havoc',
                feature_analytics: false,
                stop_serving_flags: false,
                persist_trait_data: true,
            },
        },
    };

    function flagsmithApi(eventsStatus: number) {
        const eventBatches: Array<Array<Record<string, unknown>>> = [];
        const network = vi.fn<typeof fetch>(async (input, init) => {
            const url = String(input);
            if (url.endsWith('/environment-document/')) {
                return Response.json(environmentDocument);
            }
            if (url.endsWith('/identities/')) {
                const { identifier } = JSON.parse(String(init?.body)) as { identifier: string };
                const variant = flagsmithVariant(identifier);
                return Response.json({
                    identifier,
                    traits: [],
                    flags: [
                        {
                            enabled: true,
                            feature_state_value: variant,
                            variant,
                            feature: { id: 1, name: 'study_streak_social_proof' },
                            metadata: { experiment: { id: 9, name: 'study_streak_social_proof', in_experiment: true } },
                        },
                    ],
                });
            }
            if (url.endsWith('/v1/events')) {
                eventBatches.push(
                    (JSON.parse(String(init?.body)) as { events: Array<Record<string, unknown>> }).events,
                );
                return new Response(null, { status: eventsStatus });
            }
            return new Response(null, { status: 404 });
        });
        return { network, eventBatches };
    }

    async function simulate(eventsStatus: number) {
        const api = flagsmithApi(eventsStatus);
        const delivery = createDeliveryTracker(api.network);
        const flagsmith = new Flagsmith({
            environmentKey: 'ser.simulation-test',
            enableEvents: true,
            fetch: delivery.fetch,
            eventProcessorConfig: { flushInterval: 60_000 },
        });
        const result = await runSimulation(
            flagsmith,
            { ...OPTIONS, visitors: 60 },
            {
                confirmedEvents: delivery.confirmed,
                failedEventAttempts: delivery.failedAttempts,
                now: NOW,
            },
        );
        return { ...result, ...api };
    }

    it('records exposures from Flagsmith assignment and confirms every event delivered', async () => {
        const { dataset, eventBatches, network } = await simulate(202);
        const events = eventBatches.flat();
        const exposures = events.filter((event) => event.event === '$flag_exposure');

        expect(exposures).toHaveLength(60);
        for (const exposure of exposures) {
            expect(exposure.value).toBe(flagsmithVariant(String(exposure.identifier)));
            expect(String(exposure.identifier)).toMatch(/^sim-s5-/);
        }
        const clicks = events.filter((event) => event.event === 'signup_clicked');
        for (const click of clicks) {
            const visitor = dataset.visitors.find((candidate) => candidate.visitorId === click.identifier);
            expect(Number(click.value)).toBe(visitor?.clickedAfterSeconds);
        }
        expect(dataset.run.eventDelivery.$flag_exposure).toEqual({ tracked: 60, confirmed: 60 });
        expect(dataset.run.eventDelivery.signup_clicked.confirmed).toBe(clicks.length);
        for (const [, init] of network.mock.calls.filter(([url]) => String(url).endsWith('/v1/events'))) {
            expect(new Headers(init?.headers).get('X-Environment-Key')).toBe('ser.simulation-test');
        }
    });

    it('reports rejected events as not confirmed', async () => {
        const { dataset, failedEventAttempts } = await simulate(400);

        expect(dataset.run.eventDelivery.$flag_exposure).toEqual({ tracked: 60, confirmed: 0 });
        expect(failedEventAttempts).toBeGreaterThan(0);
    });

    it('produces a dataset the supplementary analysis accepts', async () => {
        const { dataset } = await simulate(202);
        const analysis = analyseSimulatedDataset(dataset);

        expect(analysis.totalVisitors).toBe(60);
        expect(analysis.label).toBe('SIMULATED DATA — SUPPLEMENTARY ANALYSIS');
    });
});
