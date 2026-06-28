from leadengine.enrichment.website import PageBundle
from leadengine.techdetect import detector, monetization

_WP_REACT = """
<html><head>
  <meta name="generator" content="WordPress 6.5">
  <script src="https://cdn.example.com/react.production.min.js"></script>
</head><body>hi</body></html>
"""

_ADS = '<html><head><script src="https://a.adsterra.com/tag.js"></script></head></html>'
_LOCKER = '<html><body><script src="https://linkvertise.com/x.js"></script></body></html>'
_PLAIN = "<html><body><p>just text</p></body></html>"


def test_fingerprint_detects_cms_and_framework():
    techs = detector.detect(PageBundle(final_url="u", html=_WP_REACT))
    names = {t.technology for t in techs}
    assert "WordPress" in names
    assert "React" in names
    cats = {t.technology: t.category for t in techs}
    assert cats["WordPress"] == "cms"
    assert cats["React"] == "framework"


def test_fingerprint_uses_headers():
    techs = detector.detect(
        PageBundle(final_url="u", html="<html></html>", headers={"cf-ray": "abc", "server": "cloudflare"})
    )
    assert "Cloudflare" in {t.technology for t in techs}


def test_monetization_classifies_ads_and_link_lock():
    ads = monetization.detect(PageBundle(final_url="u", html=_ADS))
    assert ads.monetization_type == "ads"
    assert "Adsterra" in ads.ad_networks
    assert ads.friction_level == "medium"

    lock = monetization.detect(PageBundle(final_url="u", html=_LOCKER))
    assert lock.monetization_type == "link-lock"
    assert lock.friction_level == "high"


def test_monetization_unknown_when_no_signals():
    tags = monetization.detect(PageBundle(final_url="u", html=_PLAIN))
    assert tags.monetization_type == "unknown"
    assert tags.ad_networks == []
    assert tags.revenue_intensity_score == 0
