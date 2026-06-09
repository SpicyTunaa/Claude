import pytest
from domain_hunter.deduplicator import merge, _compute_confidence
from domain_hunter.models import DomainRecord


def make_record(domain, sources):
    return DomainRecord(domain=domain, sources=set(sources))


def test_merge_deduplicates_same_domain():
    records = [
        make_record("example.com", ["crtsh"]),
        make_record("example.com", ["hackertarget"]),
    ]
    result = merge(records)
    assert len(result) == 1
    assert result[0].sources == {"crtsh", "hackertarget"}


def test_merge_normalizes_wildcards():
    records = [
        make_record("*.example.com", ["crtsh"]),
        make_record("example.com", ["hackertarget"]),
    ]
    result = merge(records)
    assert len(result) == 1
    assert result[0].domain == "example.com"


def test_merge_case_insensitive():
    records = [
        make_record("Example.COM", ["crtsh"]),
        make_record("example.com", ["viewdns"]),
    ]
    result = merge(records)
    assert len(result) == 1


def test_merge_keeps_different_domains():
    records = [
        make_record("example.com", ["crtsh"]),
        make_record("other.com", ["crtsh"]),
    ]
    result = merge(records)
    assert len(result) == 2


def test_merge_drops_invalid():
    records = [
        make_record("", ["crtsh"]),
        make_record("nodot", ["crtsh"]),
        make_record("valid.com", ["crtsh"]),
    ]
    result = merge(records)
    assert len(result) == 1
    assert result[0].domain == "valid.com"


def test_confidence_score_single_source():
    records = [make_record("x.com", ["crtsh"])]
    result = merge(records)
    assert result[0].confidence_score == 0.9


def test_confidence_score_merge_increases():
    records = [
        make_record("x.com", ["crtsh"]),
        make_record("x.com", ["hackertarget"]),
    ]
    result = merge(records)
    # max(0.9, 0.8) + 0.05 * 1 = 0.95
    assert result[0].confidence_score == 0.95


def test_confidence_score_capped_at_one():
    records = [
        make_record("x.com", ["crtsh"]),
        make_record("x.com", ["hackertarget"]),
        make_record("x.com", ["dns_expander"]),
        make_record("x.com", ["github"]),
        make_record("x.com", ["viewdns"]),
    ]
    result = merge(records)
    assert result[0].confidence_score <= 1.0


def test_root_domain_extraction():
    records = [make_record("api.site.com", ["crtsh"])]
    result = merge(records)
    assert result[0].root_domain == "site.com"
    assert result[0].is_subdomain is True


def test_root_domain_not_subdomain():
    records = [make_record("example.com", ["crtsh"])]
    result = merge(records)
    assert result[0].root_domain == "example.com"
    assert result[0].is_subdomain is False
