import verification from './verification.json';
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
let saved = JSON.parse(localStorage.getItem(attemptKey) || 'null');
let participant = localStorage.getItem(identityKey);
if (!participant) {
    participant = crypto.randomUUID();
    localStorage.setItem(identityKey, participant);
}

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
$('proof-description').textContent =
    'Flagsmith counted these first attempts during a browser smoke test. These counts verify event delivery. Participant results are tracked separately.';
for (const [name, counts] of Object.entries(verification.variants)) {
    const row = document.createElement('tr');
    for (const value of [name, counts.n, counts.sum]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.append(cell);
    }
    $('proof-counts').append(row);
}
$('method').onclick = () => $('notes').showModal();

function refreshClock() {
    if (!active) return;
    const remaining = Math.max(0, Math.ceil((active.deadline - Date.now()) / 1000));
    $('clock').textContent = remaining + 's';
    if (remaining === 0) finish('expired');
}

function openDesk() {
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

function begin(forcePractice = false) {
    if (active) return;
    saved = JSON.parse(localStorage.getItem(attemptKey) || 'null');
    if (!forcePractice && saved && !saved.done) {
        active = saved;
        openDesk();
        return;
    }
    let measured = false;
    if (connected && !saved && !forcePractice) {
        const flag = flagsmith.getExperimentFlag(flagName);
        measured = Boolean(flag?.enabled && flag?.experiment?.inExperiment);
        lastLayout = flag?.enabled && flag.value === 'guided' ? 'guided' : 'control';
    }
    active = { layout: lastLayout, measured, deadline: Date.now() + 60000 };
    if (measured) {
        saved = active;
        localStorage.setItem(attemptKey, JSON.stringify(active));
        void flagsmith.flushEvents().catch(console.error);
    }
    openDesk();
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

async function finish(answer) {
    if (!active) return;
    clearInterval(interval);
    const attempt = active;
    active = null;
    const now = Date.now();
    const timedOut = now >= attempt.deadline;
    const correct = !timedOut && answer === 'pool';
    const seconds = Math.min(60, Math.ceil((now - attempt.deadline + 60000) / 1000));
    if (attempt.measured) {
        saved = { ...attempt, done: true };
        localStorage.setItem(attemptKey, JSON.stringify(saved));
    }
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
    if (attempt.measured && correct && connected) {
        flagsmith.trackEvent('drill_resolved');
        try {
            await flagsmith.flushEvents();
        } catch {
            $('outcome').append(' · Event delivery unconfirmed');
        }
    }
}
$('form').onsubmit = (event) => {
    event.preventDefault();
    void finish(new FormData(event.currentTarget).get('cause'));
};

async function initialise() {
    $('start').disabled = true;
    if (experimentKey) {
        try {
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
