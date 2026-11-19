import report from './rehearsal.json';
import dashboardCapture from './media/flagsmith-results.png?inline';

const $ = (id) => document.getElementById(id);
const labels = { control: 'Standard desk', guided: 'Guided desk' };
const { control, guided } = report.variants;
const enrolled = control.exposed + guided.exposed;
const percent = new Intl.NumberFormat('en-GB', { style: 'percent', maximumFractionDigits: 1 });
const signed = new Intl.NumberFormat('en-GB', { signDisplay: 'exceptZero', maximumFractionDigits: 1 });
const rate = (desk) => desk.converted / desk.exposed;

$(
    'replay-source',
).textContent = `Flagsmith measured ${enrolled} synthetic attempts. The rehearsal programmed a ${percent.format(
    report.simulated_success_rates.control,
)} success chance for the standard desk and ${percent.format(report.simulated_success_rates.guided)} for guided.`;

$(
    'allocation-description',
).textContent = `The ${report.flag} flag allocated ${report.configured_split.control}% of traffic to standard and ${report.configured_split.guided}% to guided. Each identity kept its assigned desk.`;
$('split-standard').style.width = (100 * control.exposed) / enrolled + '%';
$('assigned-control').textContent = control.exposed + ' standard';
$('assigned-guided').textContent = guided.exposed + ' guided';

for (const key of ['control', 'guided']) {
    const row = report.variants[key];
    const group = document.createElement('div');
    group.className = 'rate-row ' + key;
    const title = document.createElement('strong');
    title.textContent = labels[key];
    const count = document.createElement('span');
    count.textContent = `${row.converted} of ${row.exposed} · ${percent.format(rate(row))}`;
    const track = document.createElement('div');
    track.className = 'rate-track';
    track.setAttribute('aria-hidden', 'true');
    const fill = document.createElement('span');
    fill.style.width = 100 * rate(row) + '%';
    track.append(fill);
    group.append(title, count, track);
    $('result-bars').append(group);
}

const inference = report.guided_inference;
$('difference').textContent = signed.format(100 * (rate(guided) - rate(control))) + ' pp';
$('win-chance').textContent =
    inference.chance_to_win > 0.999 && inference.chance_to_win < 1 ? '>99.9%' : percent.format(inference.chance_to_win);
$('stat-detail').textContent = `Relative lift ${signed.format(
    100 * inference.lift,
)}% (95% credible interval ${signed.format(100 * inference.ci_low)}% to ${signed.format(100 * inference.ci_high)}%). ${
    report.allocation_check.method
}, p = ${report.allocation_check.p_value.toFixed(3)}.`;
const shipped = report.rollout;
$('rollout-checks').textContent = `${shipped.new_identities_verified} / ${shipped.new_identities_verified}`;
$('rollout-description').textContent = `After the rehearsal closed, the same flag was set to serve the ${labels[
    shipped.desk
].toLowerCase()} to ${shipped.percentage}% of users in that environment. All ${
    shipped.new_identities_verified
} fresh test identities received that desk outside the experiment.`;

const date = new Date(report.as_of);
$('replay-date').dateTime = report.as_of;
$('replay-date').textContent =
    'Captured ' + new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeZone: 'UTC' }).format(date);
$('download-results').href =
    'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2) + '\n');

$('dashboard-capture').src = dashboardCapture;
const liveDashboard = import.meta.env.MODE !== 'practice' && import.meta.env.VITE_FLAGSMITH_DASHBOARD_URL;
if (liveDashboard) {
    $('participant-dashboard').href = liveDashboard;
    $('participant-dashboard').hidden = false;
}

const steps = document.querySelectorAll('.replay-stages button');
function selectStage(stage) {
    for (const step of steps) {
        const panel = step.getAttribute('aria-controls');
        step.setAttribute('aria-pressed', String(panel === stage));
        $(panel).hidden = panel !== stage;
    }
}
for (const step of steps) step.onclick = () => selectStage(step.getAttribute('aria-controls'));
function openResults() {
    selectStage('measurement');
    $('notes').showModal();
}
$('method').onclick = openResults;
$('show-experiment').onclick = openResults;
