"""CSV exporter — deterministic column order and row ordering."""

from __future__ import annotations

import csv as _csv
from pathlib import Path


def _write_file(path: Path, rows: list[dict]) -> None:
    # Use a stable union of keys (first row defines column order; all rows share schema).
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write(out_dir: Path, leads: list[dict], contacts: list[dict]) -> list[Path]:
    leads_path = out_dir / "leads.csv"
    contacts_path = out_dir / "contacts.csv"
    _write_file(leads_path, leads)
    _write_file(contacts_path, contacts)
    return [leads_path, contacts_path]
