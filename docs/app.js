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
  return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function fmtDateTime(value) {
  if (!value) return 'Unknown';
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata'
  }).format(new Date(value));
}

function setRiskTheme(level) {
  const colour = RISK_COLOURS[level] || RISK_COLOURS.normal;
  document.getElementById('score-card').style.borderColor = colour;
  document.getElementById('risk-level').style.color = colour;
}

function renderHeader(data) {
  document.getElementById('impact-score').textContent = data.current.city.impact_score;
  document.getElementById('risk-level').textContent = data.current.city.risk_level;
  document.getElementById('briefing-headline').textContent = data.current.briefing.headline;
  document.getElementById('briefing-overview').textContent = data.current.briefing.overview;
  document.getElementById('generated-at').textContent = `Last updated: ${fmtDateTime(data.generated_at)}`;
  document.getElementById('monsoon-start').textContent = `Chronological data starts: ${data.monsoon_start_date}`;
  document.getElementById('disclaimer').textContent = data.disclaimer;
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
  (data.current.areas || []).slice(0, 10).forEach(area => {
    const colour = RISK_COLOURS[area.risk_level] || RISK_COLOURS.normal;
    const node = document.createElement('div');
    node.className = 'area';
    node.innerHTML = `
      <strong>${area.name}<span style="color:${colour}">${area.impact_score}</span></strong>
      <small class="muted">${area.zone} · ${area.risk_level.toUpperCase()} · ${area.signals.join(', ')}</small>
      <p>${area.summary}</p>
    `;
    root.appendChild(node);
  });
}

function renderSources(data) {
  const root = document.getElementById('sources');
  root.innerHTML = '';
  for (const source of data.sources || []) {
    const node = document.createElement('div');
    node.className = 'source';
    node.innerHTML = `<strong>${source.name}</strong><p class="muted">${source.type} · confidence: ${source.confidence}</p><p>${source.notes}</p>`;
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
    node.innerHTML = `<strong>${status.name}</strong><p class="muted">Status: ${status.status}</p>${ok ? '' : `<p>${status.error || 'No detail available'}</p>`}`;
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
  if (bounds.length) map.fitBounds(bounds, { padding: [30, 30] });
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
  ctx.fillText('Rainfall max mm and impact score from monsoon start', 24, 28);
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
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
  }

  ctx.strokeStyle = '#67e8f9';
  ctx.lineWidth = 3;
  ctx.beginPath();
  history.forEach((d, i) => {
    const px = x(i), py = yRain(d.rainfall_mm_max || 0);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  });
  ctx.stroke();

  ctx.strokeStyle = '#f9c74f';
  ctx.lineWidth = 3;
  ctx.beginPath();
  history.forEach((d, i) => {
    const px = x(i), py = yScore(d.impact_score || 0);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  });
  ctx.stroke();

  ctx.fillStyle = '#67e8f9'; ctx.fillText('Rainfall max', pad.left, height - 16);
  ctx.fillStyle = '#f9c74f'; ctx.fillText('Impact score', pad.left + 130, height - 16);
  ctx.fillStyle = '#9fb0bd';
  ctx.fillText(history[0].date, pad.left, height - 32);
  ctx.textAlign = 'right';
  ctx.fillText(history[history.length - 1].date, width - pad.right, height - 32);
  ctx.textAlign = 'left';
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
  } catch (error) {
    document.getElementById('briefing-headline').textContent = 'Could not load dashboard data.';
    document.getElementById('briefing-overview').textContent = error.message;
    console.error(error);
  }
}

main();
