import { InvalidDataError } from '@/lib/stats/invalid-data-error';

export const SIMULATION_KEY_VARIABLE = 'FLAGSMITH_SIMULATION_SERVER_KEY';

/**
 * Reads the Simulation server-side key. There is deliberately no fallback to any other variable, and a
 * key identical to a Production key is refused. Error messages never include key values.
 */
export function readSimulationServerKey(env: Readonly<Record<string, string | undefined>>): string {
    const key = env[SIMULATION_KEY_VARIABLE]?.trim();
    if (!key) {
        throw new InvalidDataError(
            `${SIMULATION_KEY_VARIABLE} is not set. Add the Simulation environment's server-side key to .env.local.`,
        );
    }
    if (!key.startsWith('ser.')) {
        throw new InvalidDataError(`${SIMULATION_KEY_VARIABLE} must be a server-side key (starting with "ser.").`);
    }
    const productionKeys = [env.FLAGSMITH_SERVER_KEY, env.FLAGSMITH_CLIENT_ENVIRONMENT_KEY].map((value) =>
        value?.trim(),
    );
    if (productionKeys.includes(key)) {
        throw new InvalidDataError(`${SIMULATION_KEY_VARIABLE} is the same as a Production key. Refusing to simulate.`);
    }
    return key;
}

const PRODUCTION_NAME_PATTERN = /\bprod(uction)?\b/i;

/** The environment behind the key must be named as a Simulation environment, and never as Production. */
export function assertSimulationEnvironmentName(name: string): void {
    if (PRODUCTION_NAME_PATTERN.test(name)) {
        throw new InvalidDataError(
            `The key belongs to the "${name}" environment, which looks like Production. Refusing to simulate.`,
        );
    }
    if (!/simulation/i.test(name)) {
        throw new InvalidDataError(
            `The key belongs to the "${name}" environment. The simulator only runs against an environment whose name contains "Simulation".`,
        );
    }
}
