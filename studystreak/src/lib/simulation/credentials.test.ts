import { describe, expect, it } from 'vitest';
import { InvalidDataError } from '@/lib/stats/invalid-data-error';
import { assertSimulationEnvironmentName, readSimulationServerKey } from './credentials';

describe('readSimulationServerKey', () => {
    it('returns the Simulation server-side key', () => {
        expect(readSimulationServerKey({ FLAGSMITH_SIMULATION_SERVER_KEY: ' ser.simulation ' })).toBe('ser.simulation');
    });

    it('never falls back to the Production key', () => {
        expect(() => readSimulationServerKey({ FLAGSMITH_SERVER_KEY: 'ser.production' })).toThrow('is not set');
    });

    it('rejects a client-side key', () => {
        expect(() => readSimulationServerKey({ FLAGSMITH_SIMULATION_SERVER_KEY: 'abc123' })).toThrow('server-side key');
    });

    it.each([
        { FLAGSMITH_SIMULATION_SERVER_KEY: 'ser.shared', FLAGSMITH_SERVER_KEY: 'ser.shared' },
        { FLAGSMITH_SIMULATION_SERVER_KEY: 'ser.shared', FLAGSMITH_CLIENT_ENVIRONMENT_KEY: 'ser.shared' },
    ])('refuses a key that matches a Production key', (env) => {
        expect(() => readSimulationServerKey(env)).toThrow('same as a Production key');
    });

    it('never includes the key in its errors', () => {
        try {
            readSimulationServerKey({ FLAGSMITH_SIMULATION_SERVER_KEY: 'not-a-server-secret-123' });
        } catch (error) {
            expect((error as Error).message).not.toContain('not-a-server-secret-123');
        }
    });
});

describe('assertSimulationEnvironmentName', () => {
    it.each(['Simulation', 'StudyStreak Simulation', 'simulation-env'])('accepts %s', (name) => {
        expect(() => assertSimulationEnvironmentName(name)).not.toThrow();
    });

    it.each(['Production', 'prod', 'Production Simulation', 'Staging', 'Development'])('refuses %s', (name) => {
        expect(() => assertSimulationEnvironmentName(name)).toThrow(InvalidDataError);
    });
});
