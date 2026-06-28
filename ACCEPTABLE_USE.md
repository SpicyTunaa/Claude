# Acceptable Use Policy

This tool exists to support **legitimate B2B lead generation** for a cybersecurity
consultancy by collecting **publicly available information** about online businesses.

## Public data only

The engine collects only information that is publicly published by the business itself or
by public directories/APIs (e.g. a company website, a public app listing, a public source
repository). It does **not** and **must not** be used to:

- bypass authentication or access controls;
- scan for, probe, or exploit vulnerabilities;
- brute-force credentials or enumerate private resources;
- collect private or personal data that is not publicly published for business contact;
- ignore a site's stated access rules.

## Respect for sources

- `robots.txt` is honored by default; rate limits are conservative and configurable
  per source. Do not raise limits to a level that burdens a target.
- Honor each source's Terms of Service. If a source disallows automated access, disable
  that adapter in `config/sources.yaml`.
- A rotating User-Agent identifies the bot; it is for politeness/load-spreading, not for
  evading access controls.

## Scoring is not a vulnerability ranking

The lead score reflects **data quality, business fit, and outreach readiness** — never the
severity of any security weakness. The optional monetization layer classifies how a site
earns revenue (public signals only) to help prioritize relevant outreach. Neither output
is a target list, and the tool deliberately collects no exploitability information.

## Outreach responsibilities (operator)

Collecting a public business contact does not authorize unsolicited bulk email. Before any
outreach you are responsible for complying with applicable law, including:

- **GDPR / ePrivacy (EU/UK):** have a lawful basis (e.g. legitimate interest assessment)
  for processing business-contact data; honor objections and erasure requests; keep data
  accurate and retained only as long as necessary. The `field_evidence` table records the
  public source and timestamp of every collected field to support such requests.
- **CAN-SPAM (US):** no deceptive headers/subject lines; identify the message as an
  outreach; include a valid physical postal address and a working opt-out; honor opt-outs
  promptly.
- **CASL (Canada)** and other local regimes as applicable.

## Data handling

- Treat exported leads/contacts as business data; store and share them responsibly.
- Provide opt-out/suppression handling in your outreach process and exclude suppressed
  contacts from future exports.

If in doubt about whether a use is appropriate, do not proceed.
