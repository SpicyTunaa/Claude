# Lead Discovery & Enrichment Engine

A minimal, deterministic, plugin-based engine that discovers public business leads,
enriches them, extracts public contacts, fingerprints their technology, scores them for
**data quality / business fit / outreach readiness**, and exports CSV/JSON — for
legitimate B2B cybersecurity prospecting.

**Public data only.** It respects `robots.txt` and configurable rate limits and never
performs exploitation, authentication bypass, vulnerability scanning, brute forcing, or
private-data collection. See [`ACCEPTABLE_USE.md`](ACCEPTABLE_USE.md).

> This is the **strict MVP** (Phase 1 of an agreed phased plan). Scope is intentionally
> small: one linear pipeline, SQLite, a plugin interface, a mock + one real source, and
> CSV/JSON export. It is built so new sources are a single drop-in file.

## Pipeline

```
Discovery → Enrichment → Contact Discovery → Technology Fingerprinting → Lead Scoring → Export
                                                     │
                                       (optional) Monetization Detection
```

- **Discovery** runs broad and fast, upserting leads (dedup by registrable domain).
- **Enrichment / contact / fingerprint / score** run per lead, persisting after each
  stage so an interrupted run can `resume`.
- **Monetization Detection** is an *optional, non-blocking* tagging layer inside
  fingerprinting (ad networks, monetization model, revenue intensity, friction). It never
  affects core correctness; disabled → leads carry NULL tags and scores are unchanged.

## Quickstart

```bash
make install                 # create .venv and install (Python 3.11+)
make test                    # run the offline test suite (no network)
make example                 # deterministic offline demo using the mock source
# or:
.venv/bin/leadengine list-sources
.venv/bin/leadengine run --source example
```

Outputs land in `output/` (`leads.csv`, `contacts.csv`, `leads.json`, `contacts.json`)
and the database in `data/leadengine.db`.

### Docker

```bash
docker compose up --build    # runs one full pass; writes ./data and ./output
docker run --rm leadengine:latest list-sources
```

## CLI

| Command | Description |
|---|---|
| `list-sources` | List registered adapters and whether they are enabled in config |
| `adapter-health` | Run each enabled adapter's `health_check()` |
| `run [--once] [--source NAME]` | Discover → … → export |
| `resume` | Finish processing any not-yet-exported leads, then export |
| `export` | Re-export the current DB to CSV/JSON without re-processing |
| `init-db` / `stats` / `version` | Utilities |

## Configuration (`config/`)

- `config.yaml` — database, fetcher (rate limit/retries/robots/UA rotation), enrichment,
  monetization, export, and per-source `enabled` / `rate_limit`. Override any value with
  `LEADENGINE_*` env vars (see `.env.example`).
- `categories.yaml` — the configurable category vocabulary.
- `scoring.yaml` — deterministic scoring weights (quality/fit, **not** vulnerability severity).
- `src/leadengine/techdetect/signatures.yaml` and `monetization.yaml` — detection rules.

## Adding a source

One file in `src/leadengine/adapters/sources/`, no core changes. See
[`docs/ADDING_A_SOURCE.md`](docs/ADDING_A_SOURCE.md) (target: under 30 minutes).

## Project layout

```
src/leadengine/
  core/        config, fetcher, pipeline, models, logging
  adapters/    plugin base + registry; sources/ (example, hackernews)
  enrichment/  website fetch + parse
  contact/     email + contact-link extraction
  techdetect/  rule-based fingerprinting + optional monetization layer
  scoring/     deterministic scoring engine
  storage/     SQLAlchemy schema + repository (dedup, incremental, append-only evidence)
  export/      CSV + JSON writers
  cli.py       Typer CLI
config/  tests/  docs/
```

## Determinism & resumability

- Same input → same output. Set `LEADENGINE_FROZEN_NOW` to freeze timestamps for
  byte-stable artifacts (used by tests and demos).
- Each lead's stage is a DB checkpoint; `resume` reprocesses only not-yet-exported leads.

## Roadmap (post-MVP, gated on approval)

Phase 2 real source adapters · Phase 3 deeper enrichment/fingerprinting · Phase 4 scoring
tuning, scheduling, additional export targets. None of these require core redesign.
