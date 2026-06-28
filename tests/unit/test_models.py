from leadengine.core.models import extract_host, normalize_url, registrable_domain


def test_normalize_url_adds_scheme_and_strips_trailing():
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("HTTP://Example.com/Path/") == "http://example.com/Path"
    assert normalize_url("https://x.com/a#frag") == "https://x.com/a"


def test_extract_host_drops_www_and_port():
    assert extract_host("https://www.example.com:8443/x") == "example.com"


def test_registrable_domain_simple_and_multipart():
    assert registrable_domain("https://sub.example.com/path") == "example.com"
    assert registrable_domain("https://www.example.co.uk") == "example.co.uk"
    assert registrable_domain("acme-001.example") == "acme-001.example"
    assert registrable_domain("deep.sub.example.com") == "example.com"
