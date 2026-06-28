"""JSON exporter — deterministic, pretty-printed, stable key order."""

from __future__ import annotations

import json as _json
from pathlib import Path


def write(out_dir: Path, leads: list[dict], contacts: list[dict]) -> list[Path]:
    leads_path = out_dir / "leads.json"
    contacts_path = out_dir / "contacts.json"
    leads_path.write_text(
        _json.dumps(leads, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    contacts_path.write_text(
        _json.dumps(contacts, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return [leads_path, contacts_path]
