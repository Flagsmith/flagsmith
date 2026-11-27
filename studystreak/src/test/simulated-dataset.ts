import {
    SIMULATED_DISCLOSURE,
    type EventDelivery,
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
    // In the app every signup starts from a click, so the parser rejects a signup without one.
    if (signups > clicks || clicks > count) {
        throw new RangeError(`Need signups <= clicks <= count (got ${signups}, ${clicks}, ${count}).`);
    }
    return Array.from({ length: count }, (_, index) => ({
        visitorId: `sim-${variant}-${index}`,
        variant,
        clickedAfterSeconds: index < clicks ? 2 + index : null,
        signedUp: index < signups,
    }));
}

/** Event counts that agree with the visitor records, all confirmed. */
export function eventDeliveryFor(visitors: readonly SimulatedVisitor[]): EventDelivery {
    const clicks = visitors.filter((visitor) => visitor.clickedAfterSeconds !== null).length;
    const signups = visitors.filter((visitor) => visitor.signedUp).length;
    return {
        $flag_exposure: { tracked: visitors.length, confirmed: visitors.length },
        signup_clicked: { tracked: clicks, confirmed: clicks },
        signed_up: { tracked: signups, confirmed: signups },
    };
}

/** A run for the given visitors (or a visitor count, for visitors who never clicked). */
export function simulatedRun(
    visitorsOrCount: readonly SimulatedVisitor[] | number,
    overrides: Partial<SimulationRun> = {},
): SimulationRun {
    const visitors = typeof visitorsOrCount === 'number' ? [] : visitorsOrCount;
    const visitorsRequested = typeof visitorsOrCount === 'number' ? visitorsOrCount : visitorsOrCount.length;
    const delivery = eventDeliveryFor(visitors);
    return {
        environmentName: 'Simulation',
        featureName: 'study_streak_social_proof',
        visitorsRequested,
        signupRate: { control: 0.1, social_proof: 0.12 },
        clickToSignupRate: 0.6,
        medianClickSeconds: 8,
        notEnrolled: 0,
        assignmentFailures: 0,
        eventDelivery:
            typeof visitorsOrCount === 'number'
                ? { ...delivery, $flag_exposure: { tracked: visitorsRequested, confirmed: visitorsRequested } }
                : delivery,
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
        run: simulatedRun(visitors),
        visitors,
    };
}
