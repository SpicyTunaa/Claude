import csv
from datetime import datetime
from pathlib import Path

import pytest

from domain_hunter.exporter import to_csv
from domain_hunter.models import DomainRecord, HuntResult


def make_result(records):
    return HuntResult(
        seed_domain="example.com",
        vertical="test",
        records=records,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )


def test_to_csv_creates_file(tmp_path):
    records = [
        DomainRecord("alpha.com", {"crtsh"}, is_live=True, status_code=200),
        DomainRecord("beta.com", {"hackertarget", "viewdns"}, is_live=False),
    ]
    result = make_result(records)
    path = to_csv(result, tmp_path)

    assert path.exists()
    assert path.suffix == ".csv"


def test_to_csv_correct_headers(tmp_path):
    from domain_hunter.exporter import FIELDNAMES
    result = make_result([DomainRecord("x.com", {"crtsh"})])
    path = to_csv(result, tmp_path)

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == FIELDNAMES


def test_to_csv_sources_pipe_separated(tmp_path):
    record = DomainRecord("x.com", {"crtsh", "viewdns"}, is_live=True, status_code=200)
    result = make_result([record])
    path = to_csv(result, tmp_path)

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        sources = set(row["sources"].split("|"))
        assert sources == {"crtsh", "viewdns"}


def test_to_csv_sorted_alphabetically(tmp_path):
    records = [
        DomainRecord("zebra.com", {"crtsh"}),
        DomainRecord("alpha.com", {"crtsh"}),
        DomainRecord("mango.com", {"crtsh"}),
    ]
    result = make_result(records)
    path = to_csv(result, tmp_path)

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        domains = [row["domain"] for row in reader]

    assert domains == sorted(domains)
