# Monsoon Dashboard - Mumbai

`monsoon-dashboard-mumbai` is a public, static, explainable dashboard for tracking Mumbai monsoon impact using the architecture:

```text
collectors → normalized JSON → analyzer → briefing → static dashboard
```

It is designed for GitHub Actions + GitHub Pages. GitHub Actions collects public data, normalises it into a single chronological JSON file, computes transparent impact scores, generates a public briefing, and publishes a static dashboard from `/docs`.

## Canonical data file

The project intentionally maintains **one public JSON file**:

```text
data/public/chronology.json
```

The GitHub Pages bundle copies it to:

```text
docs/data/chronology.json
```

`chronology.json` contains:

- `monsoon_start_date`
- `generated_at`
- `chronology[]`, strictly sorted by date ascending
- `current`, the latest dashboard state derived from the chronology and current forecast
- `collector_statuses`
- `sources`
- `disclaimer`

This avoids maintaining separate `history.json` and `latest.json` files that can drift out of sync.

## Workflow model

There are two workflows:

### 1. Manual seed workflow

```text
.github/workflows/seed-chronology.yml
```

Run this manually first from GitHub Actions. It creates the canonical `data/public/chronology.json` file from the configured monsoon start date through the current date.

### 2. Scheduled/manual update workflow

```text
.github/workflows/update-chronology.yml
```

This runs every 30 minutes and can also be triggered manually. It has a preflight guard: it only runs if `data/public/chronology.json` already exists. If the file does not exist, the job exits without updating data and tells you to run the seed workflow first.

## Current monsoon season anchor

The default start date is:

```text
2026-06-23
```

This is set in `config.py` because IMD's 23 June 2026 monsoon advancement note stated that the Southwest Monsoon advanced into parts of Maharashtra including Mumbai on that date. Override it without changing code when manually seeding:

```bash
MONSOON_START_DATE=2026-06-01 python scripts/seed_chronology.py
```

The generated `chronology[]` array is always written in ascending chronological order from `MONSOON_START_DATE` through the current date.


## Current-rain nowcast fix

The dashboard no longer waits only for the daily archive row to materialise. The update pipeline now uses three rainfall layers:

1. Historical daily archive values for completed days.
2. Today's daily forecast value.
3. Current/hourly rainfall nowcast values from the forecast endpoint.

For the current date only, `chronology[]` may contain a provisional row when active rainfall or the daily forecast is stronger than the archived daily value. This is marked with:

```json
{
  "provisional": true,
  "basis": "nowcast_intensity_equivalent_mm"
}
```

This keeps the timeline chronological while allowing the public dashboard to react during heavy rain before final daily rainfall data is available.

## What it shows

- Mumbai city impact score
- Current public briefing
- Explainable risk-driver scores
- Area-wise disruption map
- Highest-risk public areas
- Chronological monsoon rainfall and impact timeline
- Source confidence and disclaimers

## Important disclaimer

This is an experimental public-information project. It is not an official emergency service, disaster-management system, weather authority, traffic authority, railway status system or airport status system. For safety-critical decisions, always use official advisories from IMD, BMC, Mumbai Police, railway authorities and airport operators.

## Data sources

The V1 codebase uses no-key public sources and transparent derived signals:

| Layer | Source | Confidence | Notes |
|---|---|---:|---|
| Historical rainfall | Open-Meteo Historical Weather API | Medium | Used for chronological monsoon-season rainfall chronology. |
| Current/forecast rainfall | Open-Meteo Forecast API | Medium | Used for current and forward rainfall signals. |
| Tide | Computed semidiurnal tide estimate | Low | Non-official proxy. Replace with official tide data when available. |
| Waterlogging / traffic / rail | Derived from rainfall + area susceptibility | Derived | Transparent signal model, not official incident data. |

The project keeps source confidence visible in `chronology.json` and in the dashboard.

## Local setup

```bash
git clone https://github.com/<your-user>/monsoon-dashboard-mumbai.git
cd monsoon-dashboard-mumbai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Seed chronology locally:

```bash
python scripts/seed_chronology.py
python scripts/build_public_data.py
```

Run a normal update locally after seeding:

```bash
python scripts/run_collectors.py
python scripts/run_analyzer.py
python scripts/build_public_data.py
```

Serve the dashboard locally:

```bash
python -m http.server 8000 -d docs
```

Open:

```text
http://localhost:8000
```

## GitHub Pages deployment

1. Push the repo to GitHub.
2. Go to **Settings → Pages**.
3. Set **Build and deployment** to **Deploy from a branch**.
4. Select branch `main` and folder `/docs`.
5. Open **Actions → Seed Monsoon Chronology → Run workflow**.
6. After `chronology.json` exists, the scheduled **Update Monsoon Chronology** workflow will run every 30 minutes. It can also be run manually.

## Repository structure

```text
collectors/          public data collectors
normalizers/         source-specific raw data → common observations
analyzer/            scoring, area impact and briefing generation
scripts/             pipeline entrypoints
data/raw/            collector snapshots
data/normalized/     normalized intermediate files
data/public/         chronology.json, areas.geojson
dashboard/           source HTML/CSS/JS dashboard
docs/                GitHub Pages publish folder
tests/               lightweight tests for scoring and chronology
.github/workflows/   manual seed + guarded scheduled update workflows
```

## Scoring model

```text
impact_score =
  rainfall_score      × 0.30
+ weather_alert_score × 0.20
+ waterlogging_score  × 0.20
+ traffic_score       × 0.15
+ rail_score          × 0.10
+ tide_score          × 0.05
```

Risk bands:

| Score | Level |
|---:|---|
| 0–24 | Normal |
| 25–44 | Watch |
| 45–64 | Moderate |
| 65–79 | High |
| 80–100 | Severe |

## Replacing derived signals with official sources

The collectors are intentionally isolated. To add a source:

1. Create `collectors/collect_<source>.py` and write raw snapshots into `data/raw/`.
2. Create a matching normalizer in `normalizers/`.
3. Add the normalized signal to `analyzer/build.py`.
4. Keep confidence and source notes visible in `chronology.json`.

Good next collectors:

- BMC official disaster/waterlogging data if a stable public endpoint is available.
- Mumbai Traffic Police advisories if a stable public feed is available.
- Western/Central Railway advisories if a stable public feed is available.
- Official tide tables if a stable public endpoint is available.

## License

MIT
