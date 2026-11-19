import './experiment-replay.js';
import { updateRecord } from './attempt-store.js';
import flagsmith from '@flagsmith/flagsmith';

const $ = (id) => document.getElementById(id);
const evidence = {
    'Release log': [
        ['13:58', 'Release 8.3 healthy. Checkout p95 is 220 ms.'],
        ['14:04', 'Release 8.4 rolled out. Checkout database pool limit changed from 40 to 4 connections per worker.'],
        ['14:06', 'No changes to routing, request limits or the payment provider.'],
    ],
    Metrics: [
        ['Demand', 'Checkout traffic holds at 97–101 requests per second throughout the release.'],
        ['Database', 'Query execution p95 holds at 17 ms. All four pool connections are busy.'],
        ['Queue', 'Connection acquisition p95 rises from 8 ms to 2.61 s.'],
    ],
    Traces: [
        ['14:02', 'POST /checkout · 208 ms total · 7 ms waiting for a connection.'],
        ['14:07', 'POST /checkout · 2,866 ms total · 2,650 ms waiting for a connection.'],
        ['Payment', 'Provider authorisation takes 104 ms before the release and 108 ms after.'],
    ],
};
const answers = [
    ['provider', 'The external payment provider slowed down.'],
    ['pool', 'The release reduced the database connection pool.'],
    ['traffic', 'An unexpected traffic spike overwhelmed checkout.'],
];
const flagName = 'triage_guide';
const identityKey = 'first-minute.participant.v1';
const experimentKey = import.meta.env.MODE === 'practice' ? '' : import.meta.env.VITE_FLAGSMITH_ENVIRONMENT_ID;
const attemptKey = 'first-minute.first-attempt.v1.' + (experimentKey || 'practice');
let connected = false;
let active;
let interval;
let lastLayout = 'control';
let saved = null;

let starting = false;
const updates = experimentKey && typeof BroadcastChannel === 'function' ? new BroadcastChannel(attemptKey) : null;

function drawChart() {
    const canvas = $('chart');
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const scale = window.devicePixelRatio || 1;
    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext('2d');
    ctx.scale(scale, scale);
    ctx.strokeStyle = '#36504a';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 8; i++) {
        ctx.moveTo((width * i) / 8, 0);
        ctx.lineTo((width * i) / 8, height);
    }
    for (let i = 0; i <= 4; i++) {
        ctx.moveTo(0, (i * height) / 4);
        ctx.lineTo(width, (i * height) / 4);
    }
    ctx.stroke();
    const samples = [
        9, 10, 9, 12, 10, 12, 9, 10, 13, 10, 12, 10, 11, 10, 14, 11, 12, 11, 12, 20, 17, 34, 25, 48, 39, 72, 44, 61, 52,
        86, 63, 78, 58, 74, 69, 82, 67, 78, 75,
    ];
    ctx.beginPath();
    samples.forEach((s, i) => {
        const x = (width * i) / (samples.length - 1);
        const y = height * (1 - s / 100);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#d1f367';
    ctx.lineWidth = 2.5;
    ctx.stroke();
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    const fill = ctx.createLinearGradient(0, 0, 0, height);
    fill.addColorStop(0, '#d1f36755');
    fill.addColorStop(1, '#d1f36704');
    ctx.fillStyle = fill;
    ctx.fill();
}
new ResizeObserver(drawChart).observe($('chart'));

function selectTab(name) {
    for (const button of $('tabs').children) button.setAttribute('aria-pressed', String(button.textContent === name));
    $('signals').replaceChildren(
        ...evidence[name].map(([label, message]) => {
            const row = document.createElement('div');
            row.className = 'reading';
            const time = document.createElement('time');
            time.textContent = label;
            row.append(time, document.createTextNode(message));
            return row;
        }),
    );
}
for (const name of Object.keys(evidence)) {
    const button = document.createElement('button');
    button.textContent = name;
    button.onclick = () => selectTab(name);
    $('tabs').append(button);
}
for (const [value, answer] of answers) {
    const label = document.createElement('label');
    label.className = 'choice';
    const input = document.createElement('input');
    Object.assign(input, { type: 'radio', name: 'cause', value, required: true });
    label.append(input, document.createTextNode(' ' + answer));
    $('choices').append(label);
}
function refreshClock() {
    if (!active) return;
    const remaining = Math.max(0, Math.ceil((active.deadline - Date.now()) / 1000));
    $('clock').textContent = remaining + 's';
    if (remaining === 0) finish('expired');
}

function openDesk() {
    lastLayout = active.layout;
    $('preflight').hidden = true;
    $('desk').hidden = false;
    $('result').hidden = true;
    $('guide').hidden = active.layout !== 'guided';
    $('form').reset();
    selectTab('Release log');
    $('start').disabled = true;
    $('start').textContent = 'Drill in progress';
    $('mode').textContent = active.measured ? 'Experiment · first attempt' : 'Practice · excluded from experiment';
    $('desk').scrollIntoView({ block: 'start' });
    refreshClock();
    if (active) interval = setInterval(refreshClock, 200);
}

async function begin(forcePractice = false) {
    if (active || starting) return;
    starting = true;
    try {
        const candidate = { layout: lastLayout, measured: false, deadline: Date.now() + 60000 };
        if (connected && !forcePractice) {
            const flag = flagsmith.getAllFlags()[flagName];
            candidate.layout = flag?.enabled && flag.value === 'guided' ? 'guided' : 'control';
            candidate.measured = Boolean(flag?.enabled && flag.experiment?.inExperiment);
            if (candidate.measured) {
                try {
                    saved = await updateRecord(attemptKey, (previous) => previous ?? candidate);
                } catch {
                    active = { ...candidate, measured: false };
                    openDesk();
                    return;
                }
                if (saved === candidate) {
                    flagsmith.getExperimentFlag(flagName);
                    void flagsmith.flushEvents();
                }
                if (saved.done) candidate.measured = false;
            }
        }
        active = candidate.measured ? saved : candidate;
        openDesk();
    } finally {
        starting = false;
    }
}

function updateCapacity() {
    const connections = Number($('connections').value);
    const capacity = connections * 20; // One connection completes 1000 / 50 requests per second.
    const balance = capacity - 100;
    const outcome =
        balance < 0
            ? `Queue grows by ${-balance} requests/s.`
            : balance === 0
            ? 'Demand matches capacity, leaving no headroom.'
            : `${balance} requests/s of spare capacity.`;
    $('pool-value').value = String(connections);
    $('capacity-outcome').textContent = `${capacity} requests/s capacity. ${outcome}`;
}
$('connections').oninput = updateCapacity;

function displayResult(attempt) {
    clearInterval(interval);
    active = null;
    lastLayout = attempt.layout;
    const timedOut = attempt.answer === 'expired';
    const correct = attempt.answer === 'pool';
    const seconds = Math.min(60, Math.max(0, Math.ceil((attempt.finishedAt - attempt.deadline + 60000) / 1000)));
    $('desk').hidden = true;
    $('result').hidden = false;
    const heading = timedOut ? 'Time expired.' : correct ? 'Root cause found.' : 'Look at the connection queue.';
    $('verdict').textContent = heading;
    $('connections').value = 4;
    updateCapacity();
    $('outcome').textContent =
        seconds + 's elapsed · ' + (attempt.layout === 'guided' ? 'Guided desk' : 'Standard desk');
    $('replay').onclick = () => begin(true);
    $('switch-layout').onclick = () => {
        lastLayout = attempt.layout === 'guided' ? 'control' : 'guided';
        begin(true);
    };
    $('start').disabled = false;
    $('start').textContent = 'Practise again →';
    $('start').onclick = () => begin(true);
    $('mode').textContent = 'Debrief ready';
    $('result').focus();
}

async function finish(answer) {
    if (!active) return;
    const finishedAt = Date.now();
    const outcome = { ...active, done: true, finishedAt, answer: finishedAt >= active.deadline ? 'expired' : answer };
    clearInterval(interval);
    active = null;
    let first = outcome;
    if (outcome.measured) {
        try {
            first = await updateRecord(attemptKey, (previous) => (previous?.done ? previous : outcome));
        } catch {
            displayResult(outcome);
            $('outcome').append(' · First attempt could not be saved');
            return;
        }
        if (first === outcome) updates?.postMessage(outcome);
        saved = first;
    }
    displayResult(first.finishedAt ? first : outcome);
    if (first === outcome && outcome.measured && outcome.answer === 'pool') {
        if (!connected) {
            $('outcome').append(' · Event delivery unconfirmed');
            return;
        }
        flagsmith.trackEvent('drill_resolved');
        try {
            await flagsmith.flushEvents();
        } catch {
            $('outcome').append(' · Event delivery unconfirmed');
        }
    }
}
if (updates)
    updates.onmessage = ({ data }) => {
        if (active?.measured && data.done && data.finishedAt && data.deadline === active.deadline) {
            saved = data;
            displayResult(data);
        }
    };
$('form').onsubmit = (event) => {
    event.preventDefault();
    void finish(new FormData(event.currentTarget).get('cause'));
};

async function initialise() {
    $('start').disabled = true;
    if (experimentKey) {
        try {
            const participant = await updateRecord(
                identityKey,
                (previous) => previous || crypto.randomUUID(),
                (value) => value,
            );
            saved = await updateRecord(attemptKey, (previous) => previous);
            const remote = import.meta.env.VITE_FLAGSMITH_ORIGIN;
            const root = remote || location.origin;
            await flagsmith.init({
                environmentID: experimentKey,
                identity: participant,
                enableEvents: true,
                api: root + '/api/v1/',
                eventProcessorConfig: { eventsApiUrl: root + '/api/' },
            });
            connected = Boolean(flagsmith.getAllFlags()[flagName]);
        } catch (error) {
            console.warn('Experiment unavailable.', error);
        }
    }
    $('start').onclick = () => begin(Boolean(saved));
    $('start').disabled = false;
    if (saved && !saved.done) {
        active = saved;
        lastLayout = saved.layout;
        openDesk();
        return;
    }
    if (saved?.done && saved.finishedAt) {
        displayResult(saved);
        return;
    }
    if (saved) {
        lastLayout = saved.layout;
        $('start').textContent = 'Enter practice →';
    }
    $('mode').textContent = saved
        ? 'First attempt complete · practice available'
        : connected
        ? 'Connected to Flagsmith'
        : 'Practice mode · experiment offline';
}
void initialise();
