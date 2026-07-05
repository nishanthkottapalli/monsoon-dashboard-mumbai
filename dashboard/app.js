const RISK_COLOURS = {
  normal: '#60d394',
  watch: '#f9c74f',
  moderate: '#f8961e',
  high: '#f3722c',
  severe: '#f94144'
};

async function loadJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

function titleCase(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

function fmtDateTime(value) {
  if (!value) return 'Unknown';
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata'
  }).format(new Date(value));
}

function fmtNumber(value, digits = 1) {
  const number = Number(value || 0);
  return Number.isInteger(number) ? String(number) : number.toFixed(digits);
}

function setRiskTheme(level) {
  const colour = RISK_COLOURS[level] || RISK_COLOURS.normal;
  document.getElementById('score-card').style.borderColor = colour;
  document.getElementById('risk-level').style.color = colour;
}

function isNowcastEquivalent(row) {
  return Boolean(
    row &&
    row.provisional &&
    row.basis === 'nowcast_intensity_equivalent_mm'
  );
}

function rainfallLabel(row) {
  if (isNowcastEquivalent(row)) {
    return `Nowcast-equivalent rain signal: ${fmtNumber(row.rainfall_mm_max)} mm`;
  }

  return `Daily rainfall max: ${fmtNumber(row?.rainfall_mm_max)} mm`;
}

function rainfallShortLabel(row) {
  if (isNowcastEquivalent(row)) {
    return `${fmtNumber(row.rainfall_mm_max)} mm equivalent`;
  }

  return `${fmtNumber(row?.rainfall_mm_max)} mm`;
}

function rainfallBasisNote(row) {
  if (isNowcastEquivalent(row)) {
    return 'Provisional current-day value derived from nowcast rainfall intensity, not an official measured 24-hour rainfall total.';
  }

  return 'Historical daily rainfall value.';
}

function buildRainSignalPanel(data) {
  const signal = data.current?.rainfall_signal;
  if (!signal) return null;

  const panel = document.createElement('div');
  panel.className = 'source';
  panel.style.marginTop = '1rem';

  const basis = signal.basis || 'unknown';
  const nowcast = signal.nowcast || {};
  const isEquivalent = basis === 'nowcast_intensity_equivalent_mm';

  const title = isEquivalent ? 'Today rain signal' : 'Today rainfall';
  const value = isEquivalent
    ? `${fmtNumber(signal.value_mm)} mm equivalent`
    : `${fmtNumber(signal.value_mm)} mm`;

  const note = isEquivalent
    ? 'Derived from current-hour and recent rainfall intensity. This is an operational disruption signal, not an official 24-hour measured rainfall total.'
    : 'Based on the currently selected rainfall signal.';

  const extra = isEquivalent
    ? `
      <p class="muted">
        Current hour: ${fmtNumber(nowcast.current_hour_mm)} mm ·
        Recent 3h: ${fmtNumber(nowcast.recent_3h_mm)} mm ·
        Today forecast: ${fmtNumber(signal.today_forecast_mm)} mm
      </p>
    `
    : '';

  panel.innerHTML = `
    <strong>${title}: ${value}</strong>
    <p class="muted">Basis: ${basis}</p>
    <p>${note}</p>
    ${extra}
  `;

  return panel;
}

function renderHeader(data) {
  document.getElementById('impact-score').textContent = data.current.city.impact_score;
  document.getElementById('risk-level').textContent = data.current.city.risk_level;
  document.getElementById('briefing-headline').textContent = data.current.briefing.headline;
  document.getElementById('briefing-overview').textContent = data.current.briefing.overview;
  document.getElementById('generated-at').textContent = `Last updated: ${fmtDateTime(data.generated_at)}`;
  document.getElementById('monsoon-start').textContent = `Chronological data starts: ${data.monsoon_start_date}`;
  document.getElementById('disclaimer').textContent = data.disclaimer;

  const briefingPanel = document.getElementById('briefing-overview')?.parentElement;
  const existingSignal = document.getElementById('rain-signal-panel');
  if (existingSignal) existingSignal.remove();

  const rainSignalPanel = buildRainSignalPanel(data);
  if (briefingPanel && rainSignalPanel) {
    rainSignalPanel.id = 'rain-signal-panel';
    const advisory = document.getElementById('public-advisory');
    briefingPanel.insertBefore(rainSignalPanel, advisory);
  }

  const ul = document.getElementById('public-advisory');
  ul.innerHTML = '';
  for (const item of data.current.briefing.public_advisory || []) {
    const li = document.createElement('li');
    li.textContent = item;
    ul.appendChild(li);
  }

  setRiskTheme(data.current.city.risk_level);
}

function renderDrivers(data) {
  const root = document.getElementById('drivers');
  root.innerHTML = '';

  Object.entries(data.current.drivers || {}).forEach(([name, driver]) => {
    const colour = RISK_COLOURS[driver.level] || RISK_COLOURS.normal;
    const node = document.createElement('div');
    node.className = 'driver';

    node.innerHTML = `
      <strong>${titleCase(name)}</strong>
      <span class="badge" style="background:${colour}22;color:${colour}">${driver.score} · ${driver.level}</span>
      <div class="bar"><span style="width:${driver.score}%;background:${colour}"></span></div>
      <small class="muted">Confidence: ${driver.confidence}</small>
    `;

    root.appendChild(node);
  });
}

function renderAreas(data) {
  const root = document.getElementById('areas');
  root.innerHTML = '';

  const areas = [...(data.current.areas || [])].sort((a, b) => {
    const scoreDiff = Number(b.impact_score || 0) - Number(a.impact_score || 0);
    if (scoreDiff !== 0) return scoreDiff;

    const susceptibilityDiff = Number(b.susceptibility || 0) - Number(a.susceptibility || 0);
    if (susceptibilityDiff !== 0) return susceptibilityDiff;

    return String(a.name || '').localeCompare(String(b.name || ''));
  });

  for (const area of areas) {
    const colour = RISK_COLOURS[area.risk_level] || RISK_COLOURS.normal;
    const node = document.createElement('div');
    node.className = 'area';

    node.innerHTML = `
      <strong>
        ${area.name}
        <span style="color:${colour}">${area.impact_score}</span>
      </strong>
      <small class="muted">
        ${area.zone} · ${area.risk_level.toUpperCase()} ·
        susceptibility ${fmtNumber(area.susceptibility, 2)} ·
        ${area.signals.join(', ')}
      </small>
      <p>${area.summary}</p>
    `;

    root.appendChild(node);
  }
}

function renderSources(data) {
  const root = document.getElementById('sources');
  root.innerHTML = '';

  for (const source of data.sources || []) {
    const node = document.createElement('div');
    node.className = 'source';
    node.innerHTML = `
      <strong>${source.name}</strong>
      <p class="muted">${source.type} · confidence: ${source.confidence}</p>
      <p>${source.notes}</p>
    `;
    root.appendChild(node);
  }
}

function renderCollectorStatuses(data) {
  const root = document.getElementById('collector-statuses');
  if (!root) return;

  root.innerHTML = '';

  for (const status of data.collector_statuses || []) {
    const ok = status.status === 'ok';
    const node = document.createElement('div');
    node.className = 'source';

    node.innerHTML = `
      <strong>${status.name}</strong>
      <p class="muted">Status: ${status.status}</p>
      ${ok ? '' : `<p>${status.error || 'No detail available'}</p>`}
    `;

    root.appendChild(node);
  }
}

function renderMap(data) {
  const map = L.map('map', { zoomControl: true }).setView([19.076, 72.8777], 11);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  const bounds = [];

  for (const area of data.current.areas || []) {
    const colour = RISK_COLOURS[area.risk_level] || RISK_COLOURS.normal;

    const marker = L.circleMarker([area.lat, area.lon], {
      radius: 8 + area.impact_score / 18,
      color: colour,
      fillColor: colour,
      fillOpacity: 0.55,
      weight: 2
    }).addTo(map);

    marker.bindPopup(`
      <strong>${area.name}</strong><br />
      ${area.zone}<br />
      Score: ${area.impact_score} (${area.risk_level})<br />
      ${area.summary}
    `);

    bounds.push([area.lat, area.lon]);
  }

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [30, 30] });
  }
}

function renderHistory(data) {
  const canvas = document.getElementById('history-chart');
  const ctx = canvas.getContext('2d');
  const history = data.chronology || [];
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);
  ctx.font = '14px system-ui';
  ctx.fillStyle = '#9fb0bd';
  ctx.fillText('Rainfall / nowcast signal and impact score from monsoon start', 24, 28);

  if (!history.length) {
    ctx.fillText('No history available yet.', 24, 70);
    return;
  }

  const pad = { left: 48, right: 24, top: 56, bottom: 48 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const maxRain = Math.max(100, ...history.map(d => d.rainfall_mm_max || 0));

  const x = i => pad.left + (history.length === 1 ? 0 : (i / (history.length - 1)) * innerW);
  const yRain = mm => pad.top + innerH - (mm / maxRain) * innerH;
  const yScore = score => pad.top + innerH - (score / 100) * innerH;

  ctx.strokeStyle = 'rgba(255,255,255,.12)';
  ctx.lineWidth = 1;

  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (i / 4) * innerH;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(width - pad.right, y);
    ctx.stroke();
  }

  ctx.strokeStyle = '#67e8f9';
  ctx.lineWidth = 3;
  ctx.beginPath();

  history.forEach((d, i) => {
    const px = x(i);
    const py = yRain(d.rainfall_mm_max || 0);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  });

  ctx.stroke();

  ctx.strokeStyle = '#f9c74f';
  ctx.lineWidth = 3;
  ctx.beginPath();

  history.forEach((d, i) => {
    const px = x(i);
    const py = yScore(d.impact_score || 0);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  });

  ctx.stroke();

  const latest = history[history.length - 1];

  ctx.fillStyle = '#67e8f9';
  ctx.fillText('Rainfall / nowcast signal', pad.left, height - 16);

  ctx.fillStyle = '#f9c74f';
  ctx.fillText('Impact score', pad.left + 205, height - 16);

  ctx.fillStyle = '#9fb0bd';
  ctx.fillText(history[0].date, pad.left, height - 32);

  ctx.textAlign = 'right';
  ctx.fillText(history[history.length - 1].date, width - pad.right, height - 32);
  ctx.textAlign = 'left';

  ctx.fillStyle = '#9fb0bd';
  ctx.fillText(`Latest: ${rainfallShortLabel(latest)}`, pad.left + 360, height - 16);

  if (isNowcastEquivalent(latest)) {
    ctx.fillStyle = '#f9c74f';
    ctx.fillText('Latest point is provisional nowcast-equivalent signal.', pad.left + 360, height - 32);
  }
}

function renderLatestChronologyNote(data) {
  const history = data.chronology || [];
  const latest = history[history.length - 1];

  const canvas = document.getElementById('history-chart');
  if (!canvas || !latest) return;

  let note = document.getElementById('history-signal-note');
  if (!note) {
    note = document.createElement('p');
    note.id = 'history-signal-note';
    note.className = 'muted';
    canvas.insertAdjacentElement('afterend', note);
  }

  note.textContent = `${rainfallLabel(latest)}. ${rainfallBasisNote(latest)}`;
}

async function main() {
  try {
    const data = await loadJson('data/chronology.json');

    renderHeader(data);
    renderDrivers(data);
    renderAreas(data);
    renderSources(data);
    renderCollectorStatuses(data);
    renderMap(data);
    renderHistory(data);
    renderLatestChronologyNote(data);
  } catch (error) {
    document.getElementById('briefing-headline').textContent = 'Could not load dashboard data.';
    document.getElementById('briefing-overview').textContent = error.message;
    console.error(error);
  }
}

main();
