const LANCZOS_COEFFICIENTS = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
];

// Lanczos approximation (g = 7), accurate to about 15 significant digits for x > 0.
export function logGamma(x: number): number {
    if (x < 0.5) {
        return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
    }
    const shifted = x - 1;
    let series = 0.99999999999980993;
    LANCZOS_COEFFICIENTS.forEach((coefficient, index) => {
        series += coefficient / (shifted + index + 1);
    });
    const t = shifted + LANCZOS_COEFFICIENTS.length - 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (shifted + 0.5) * Math.log(t) - t + Math.log(series);
}

export function logBeta(a: number, b: number): number {
    return logGamma(a) + logGamma(b) - logGamma(a + b);
}

// Continued fraction for the incomplete beta function (modified Lentz's method).
function incompleteBetaFraction(x: number, a: number, b: number): number {
    const tiny = 1e-300;
    let c = 1;
    let d = 1 - ((a + b) * x) / (a + 1);
    d = 1 / (Math.abs(d) < tiny ? tiny : d);
    let fraction = d;
    for (let m = 1; m <= 500; m++) {
        const twoM = 2 * m;
        const even = (m * (b - m) * x) / ((a + twoM - 1) * (a + twoM));
        d = 1 / (Math.abs(1 + even * d) < tiny ? tiny : 1 + even * d);
        c = Math.abs(1 + even / c) < tiny ? tiny : 1 + even / c;
        fraction *= d * c;
        const odd = (-(a + m) * (a + b + m) * x) / ((a + twoM) * (a + twoM + 1));
        d = 1 / (Math.abs(1 + odd * d) < tiny ? tiny : 1 + odd * d);
        c = Math.abs(1 + odd / c) < tiny ? tiny : 1 + odd / c;
        const delta = d * c;
        fraction *= delta;
        if (Math.abs(delta - 1) < 1e-15) {
            break;
        }
    }
    return fraction;
}

/** Regularised incomplete beta function I_x(a, b): the CDF of Beta(a, b) at x. */
export function betaCdf(x: number, a: number, b: number): number {
    if (x <= 0) {
        return 0;
    }
    if (x >= 1) {
        return 1;
    }
    const logFront = a * Math.log(x) + b * Math.log(1 - x) - logBeta(a, b);
    // The continued fraction converges fastest on this side of the mean.
    if (x < (a + 1) / (a + b + 2)) {
        return (Math.exp(logFront) * incompleteBetaFraction(x, a, b)) / a;
    }
    return 1 - (Math.exp(logFront) * incompleteBetaFraction(1 - x, b, a)) / b;
}

/** Inverse CDF of Beta(a, b), by bisection to within 1e-12. */
export function betaQuantile(probability: number, a: number, b: number): number {
    let low = 0;
    let high = 1;
    while (high - low > 1e-12) {
        const middle = (low + high) / 2;
        if (betaCdf(middle, a, b) < probability) {
            low = middle;
        } else {
            high = middle;
        }
    }
    return (low + high) / 2;
}

/**
 * Exact P(X_B > X_A) for X_A ~ Beta(alphaA, betaA) and X_B ~ Beta(alphaB, betaB), with integer alphaB
 * (Evan Miller's closed form). Each term is summed in log space to avoid overflow.
 */
export function probabilityBExceedsA(alphaA: number, betaA: number, alphaB: number, betaB: number): number {
    if (!Number.isInteger(alphaB)) {
        throw new RangeError('alphaB must be an integer for the closed-form solution.');
    }
    let total = 0;
    for (let i = 0; i < alphaB; i++) {
        total += Math.exp(
            logBeta(alphaA + i, betaA + betaB) - Math.log(betaB + i) - logBeta(1 + i, betaB) - logBeta(alphaA, betaA),
        );
    }
    return Math.min(1, Math.max(0, total));
}
