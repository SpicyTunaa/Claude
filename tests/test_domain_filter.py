import pytest
from domain_hunter.validators.domain_filter import is_valid, apply
from domain_hunter.models import DomainRecord


def record(domain):
    return DomainRecord(domain=domain, sources={"crtsh"})


def test_valid_domain():
    assert is_valid("example.com")
    assert is_valid("sub.example.co.uk")
    assert is_valid("my-domain.net")


def test_invalid_empty():
    assert not is_valid("")
    assert not is_valid(None)


def test_invalid_ptr():
    assert not is_valid("1.0.0.10.in-addr.arpa")


def test_invalid_no_tld():
    assert not is_valid("nodot")
    assert not is_valid("only-dash-")


def test_cdn_noise_filtered():
    assert not is_valid("some.cloudflare.com")
    assert not is_valid("bucket.amazonaws.com")


def test_apply_filters_list():
    records = [
        record("valid.com"),
        record("1.2.3.4.in-addr.arpa"),
        record(""),
        record("some.cloudfront.net"),
        record("another.valid.io"),
    ]
    result = apply(records)
    domains = {r.domain for r in result}
    assert "valid.com" in domains
    assert "another.valid.io" in domains
    assert len(result) == 2
