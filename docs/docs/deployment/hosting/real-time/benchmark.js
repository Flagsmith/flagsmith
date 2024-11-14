// Stress test for the Flagsmith SSE service
// https://docs.flagsmith.com/deployment/hosting/real-time

import { sleep } from 'k6';
import http from 'k6/http';
import exec from 'k6/execution';

export const options = {
    discardResponseBodies: true,
    scenarios: {
        // Gradually ramp up to 20k concurrent subscribers for the same environment
        subscribe: {
            exec: 'subscribers',
            executor: 'ramping-vus',
            stages: [{ duration: '1m', target: 20000 }],
        },
        // Publish an update to the same environment every 10s
        publish: {
            duration: '1m',
            exec: 'publish',
            executor: 'constant-vus',
            vus: 1,
        },
    },
};

const env = 'load_test';
export function subscribers() {
    http.get(`http://localhost:8088/sse/environments/${env}/queue-change`, '', {
        headers: {
            Accept: 'event/stream',
        },
        timeout: '3m',
    });
}

export function publish() {
    const body = JSON.stringify({
        updated_at: exec.vu.iterationInScenario,
    });
    http.post(`http://localhost:8088/sse/environments/${env}/queue-change`, body, {
        headers: {
            'Content-Type': 'application/json',
            Authorization: 'Token ' + __ENV.SSE_AUTHENTICATION_TOKEN,
        },
    });
    sleep(10);
}
