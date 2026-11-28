export type Random = () => number;

// mulberry32: a small, fast, seedable PRNG with uniform output in [0, 1).
export function createRandom(seed: number): Random {
    let state = seed >>> 0;
    return () => {
        state = (state + 0x6d2b79f5) >>> 0;
        let t = state;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function standardNormal(random: Random): number {
    const u = 1 - random();
    const v = random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// Marsaglia and Tsang (2000), valid for shape >= 1; posterior shapes here are always at least 1.
function sampleGamma(shape: number, random: Random): number {
    const d = shape - 1 / 3;
    const c = 1 / Math.sqrt(9 * d);
    for (;;) {
        let x: number;
        let v: number;
        do {
            x = standardNormal(random);
            v = 1 + c * x;
        } while (v <= 0);
        v = v * v * v;
        const u = 1 - random();
        if (Math.log(u) < 0.5 * x * x + d - d * v + d * Math.log(v)) {
            return d * v;
        }
    }
}

export function sampleBeta(alpha: number, beta: number, random: Random): number {
    const x = sampleGamma(alpha, random);
    return x / (x + sampleGamma(beta, random));
}
