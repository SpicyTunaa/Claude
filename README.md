# Domain Hunter v2

Automated domain discovery tool using 8 free sources. Give it a seed domain and vertical, get back a deduplicated CSV of related domains with live-status validation.

## Sources

| Source | Method | Limit |
|--------|--------|-------|
| crt.sh | Certificate transparency API | None |
| HackerTarget | Reverse IP lookup | 100/day |
| ViewDNS | Reverse IP scrape | Polite |
| DuckDuckGo | Web scrape | Polite |
| Yandex | Web scrape | Polite |
| Reddit | JSON search API | 30 req/min |
| GitHub | Code search API | 10/min (60 with token) |
| DNS Expander | NS/MX sibling lookup | Uses HackerTarget quota |

## Setup

```bash
git clone <repo>
cd domain_hunter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env as needed
```

## CLI Usage

```bash
# Basic hunt
python -m domain_hunter.cli hunt example.com adtech

# Skip HTTP validation (faster)
python -m domain_hunter.cli hunt example.com adtech --no-validate

# Verbose logging
python -m domain_hunter.cli hunt example.com adtech --verbose

# Custom output directory
python -m domain_hunter.cli hunt example.com adtech --output ./results

# Re-validate an existing CSV
python -m domain_hunter.cli validate ./output/example_com_adtech_20260609.csv
```

## Output CSV

| Column | Description |
|--------|-------------|
| domain | Discovered domain |
| sources | Pipe-separated source names |
| is_live | True/False (HTTP 2xx/3xx) |
| status_code | HTTP status code |
| discovered_at | ISO timestamp |

## Telegram Bot

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_CHAT_IDS` in `.env`, then:

```bash
python -m bot.telegram_bot
```

Commands: `/hunt <domain> <vertical>`, `/status`, `/help`

## Cron Job

```bash
# Edit cron/crontab.example with correct paths, then:
crontab -e
# Paste the cron line
```

Seeds file format (`seeds.txt`): one `domain,vertical` per line.

## Tests

```bash
pytest tests/ -v
```

## Environment Variables

See `.env.example` for all options. Key ones:

- `GITHUB_TOKEN` — enables GitHub hunter (optional)
- `TELEGRAM_BOT_TOKEN` — enables Telegram bot
- `HACKERTARGET_DAILY_QUOTA` — default 100 (free tier)
- `DISABLED_HUNTERS` — comma-separated hunter names to skip
