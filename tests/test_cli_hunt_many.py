import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from domain_hunter.cli import _parse_seeds, hunt_many


def test_parse_seeds_valid(tmp_path):
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("example.com,adtech\nother.io,gaming\n")
    result = _parse_seeds(seeds_file)
    assert result == [("example.com", "adtech"), ("other.io", "gaming")]


def test_parse_seeds_skips_comments(tmp_path):
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("# comment\nexample.com,adtech\n\n")
    result = _parse_seeds(seeds_file)
    assert result == [("example.com", "adtech")]


def test_parse_seeds_skips_invalid_lines(tmp_path):
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("nodomain\nexample.com,adtech\n")
    result = _parse_seeds(seeds_file)
    assert result == [("example.com", "adtech")]


def test_parse_seeds_empty_file(tmp_path):
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("")
    result = _parse_seeds(seeds_file)
    assert result == []


def test_hunt_many_runs_sequentially(tmp_path):
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("example.com,adtech\n")

    from domain_hunter.models import HuntResult
    from datetime import datetime

    mock_result = MagicMock(spec=HuntResult)
    mock_result.records = []
    mock_result.started_at = datetime.utcnow()
    mock_result.finished_at = datetime.utcnow()

    runner = CliRunner()
    with patch("domain_hunter.cli.run_hunt", new=AsyncMock(return_value=mock_result)), \
         patch("domain_hunter.cli.to_csv", return_value=tmp_path / "out.csv"):
        result = runner.invoke(hunt_many, [str(seeds_file), "--output", str(tmp_path), "--no-validate"])

    assert result.exit_code == 0
