from leadengine.contact.extract import extract_contacts
from leadengine.core.models import Lead
from leadengine.enrichment.website import PageBundle

_HTML = """
<html><body>
  <a href="mailto:support@acme.example">support</a>
  <a href="mailto:security@acme.example">security</a>
  <a href="/contact">Contact us</a>
  Reach sales@acme.example for pricing.
</body></html>
"""


def _lead():
    return Lead(registrable_domain="acme.example", website="https://acme.example")


def test_extract_and_prioritize_contacts():
    lead = _lead()
    bundle = PageBundle(final_url="https://acme.example", html=_HTML)
    evidence = extract_contacts(lead, bundle, source="test")

    emails = [c.email for c in lead.contacts]
    assert "security@acme.example" in emails
    assert "support@acme.example" in emails
    assert "sales@acme.example" in emails
    # security@ must be prioritized first.
    assert lead.contacts[0].email == "security@acme.example"
    assert lead.contacts[0].type == "security"
    assert all(c.validation_status == "valid" for c in lead.contacts)
    assert any(e.field == "contact_page" for e in evidence)


def test_no_emails_yields_no_contacts():
    lead = _lead()
    bundle = PageBundle(final_url="https://acme.example", html="<html><p>nothing</p></html>")
    extract_contacts(lead, bundle, source="test")
    assert lead.contacts == []
