import {
    SIMULATED_DISCLOSURE,
    type SimulatedDataset,
    type SimulatedVisitor,
    type SimulationRun,
    type Variant,
} from '@/lib/simulation/dataset';

export function simulatedVisitors(
    variant: Variant,
    count: number,
    clicks: number,
    signups: number,
): SimulatedVisitor[] {
    return Array.from({ length: count }, (_, index) => ({
        visitorId: `sim-${variant}-${index}`,
        variant,
        clickedAfterSeconds: index < clicks ? 2 + index : null,
        signedUp: index < signups,
    }));
}

export function simulatedRun(visitorsRequested: number, overrides: Partial<SimulationRun> = {}): SimulationRun {
    return {
        environmentName: 'Simulation',
        featureName: 'study_streak_social_proof',
        visitorsRequested,
        signupRate: { control: 0.1, social_proof: 0.12 },
        clickToSignupRate: 0.6,
        medianClickSeconds: 8,
        notEnrolled: 0,
        assignmentFailures: 0,
        eventDelivery: {
            $flag_exposure: { tracked: visitorsRequested, confirmed: visitorsRequested },
            signup_clicked: { tracked: 0, confirmed: 0 },
            signed_up: { tracked: 0, confirmed: 0 },
        },
        ...overrides,
    };
}

export function simulatedDataset(visitors: SimulatedVisitor[], seed = 7): SimulatedDataset {
    return {
        kind: 'simulated',
        environment: 'simulation',
        disclosure: SIMULATED_DISCLOSURE,
        seed,
        generatedAt: '2026-11-26T12:00:00.000Z',
        run: simulatedRun(visitors.length),
        visitors,
    };
}
