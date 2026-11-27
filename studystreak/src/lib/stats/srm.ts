export const SRM_P_VALUE_THRESHOLD = 0.001;
export const SRM_MINIMUM_VISITORS = 100;

export type SampleRatioCheck =
    | { status: 'not_checked'; reason: string; control: number; treatment: number; expectedShare: number }
    | {
          status: 'ok' | 'mismatch';
          control: number;
          treatment: number;
          expectedShare: number;
          expectedControl: number;
          expectedTreatment: number;
          chiSquare: number;
          pValue: number;
      };

// Complementary error function (Numerical Recipes erfcc), fractional error below 1.2e-7.
function erfc(x: number): number {
    const z = Math.abs(x);
    const t = 1 / (1 + 0.5 * z);
    const result =
        t *
        Math.exp(
            -z * z -
                1.26551223 +
                t *
                    (1.00002368 +
                        t *
                            (0.37409196 +
                                t *
                                    (0.09678418 +
                                        t *
                                            (-0.18628806 +
                                                t *
                                                    (0.27886807 +
                                                        t *
                                                            (-1.13520398 +
                                                                t *
                                                                    (1.48851587 +
                                                                        t * (-0.82215223 + t * 0.17087277)))))))),
        );
    return x >= 0 ? result : 2 - result;
}

/**
 * Chi-square goodness-of-fit test (1 degree of freedom) of the observed split against the configured
 * treatment share. A p-value below 0.001 flags a sample ratio mismatch, the threshold Flagsmith documents.
 */
export function checkSampleRatio(control: number, treatment: number, expectedTreatmentShare = 0.5): SampleRatioCheck {
    const total = control + treatment;
    if (total < SRM_MINIMUM_VISITORS) {
        return {
            status: 'not_checked',
            reason: `Needs at least ${SRM_MINIMUM_VISITORS} visitors.`,
            control,
            treatment,
            expectedShare: expectedTreatmentShare,
        };
    }
    // A boundary share makes one expected count zero, and the statistic NaN, which would read as "ok".
    if (!(expectedTreatmentShare > 0 && expectedTreatmentShare < 1)) {
        return {
            status: 'not_checked',
            reason: `The expected treatment share must be strictly between 0 and 1 (got ${expectedTreatmentShare}).`,
            control,
            treatment,
            expectedShare: expectedTreatmentShare,
        };
    }
    const expectedTreatment = total * expectedTreatmentShare;
    const expectedControl = total - expectedTreatment;
    const chiSquare =
        (control - expectedControl) ** 2 / expectedControl + (treatment - expectedTreatment) ** 2 / expectedTreatment;
    // For one degree of freedom, P(chi-square > x) = erfc(sqrt(x / 2)).
    const pValue = erfc(Math.sqrt(chiSquare / 2));
    return {
        status: pValue < SRM_P_VALUE_THRESHOLD ? 'mismatch' : 'ok',
        control,
        treatment,
        expectedShare: expectedTreatmentShare,
        expectedControl,
        expectedTreatment,
        chiSquare,
        pValue,
    };
}
