"""Contact extraction: emails from mailto links and page text, plus contact-page links.

Public data only. Emails are validated for syntax and classified/prioritised by mailbox
(security > support > sales > info > generic).
"""

from __future__ import annotations

import re

from email_validator import EmailNotValidError, validate_email

from ..core.models import Contact, FieldValue, Lead
from ..enrichment.website import PageBundle, _soup

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# Mailbox prefix -> (type, priority weight). Higher priority sorts first.
_TYPE_RULES: list[tuple[str, str, int]] = [
    ("security", "security", 100),
    ("abuse", "security", 90),
    ("support", "support", 80),
    ("help", "support", 75),
    ("hello", "generic", 70),
    ("contact", "generic", 65),
    ("sales", "sales", 60),
    ("info", "info", 55),
    ("admin", "generic", 40),
]


def _classify(email: str) -> tuple[str, int]:
    local = email.split("@", 1)[0].lower()
    for prefix, ctype, weight in _TYPE_RULES:
        if local == prefix or local.startswith(prefix):
            return ctype, weight
    return "generic", 30


def _validate(email: str) -> str:
    try:
        validate_email(email, check_deliverability=False)
        return "valid"
    except EmailNotValidError:
        return "invalid"


def extract_contacts(lead: Lead, bundle: PageBundle, *, source: str) -> list[FieldValue]:
    """Find public emails + contact-page links. Mutates ``lead.contacts``. Returns evidence."""
    soup = _soup(bundle.html)
    found: dict[str, str] = {}  # email -> raw context

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            addr = href[7:].split("?", 1)[0].strip()
            if _EMAIL_RE.fullmatch(addr):
                found.setdefault(addr.lower(), href)

    for match in _EMAIL_RE.findall(bundle.html):
        found.setdefault(match.lower(), match)

    evidence: list[FieldValue] = []
    existing = {c.email for c in lead.contacts}
    for email in sorted(found):
        status = _validate(email)
        if status == "invalid":
            continue
        ctype, weight = _classify(email)
        if email not in existing:
            lead.contacts.append(
                Contact(
                    email=email,
                    type=ctype,
                    validation_status=status,
                    source=source,
                    confidence=0.7 if href_is_mailto(found[email]) else 0.5,
                )
            )
            existing.add(email)
        evidence.append(
            FieldValue(
                field="contact_email",
                value=email,
                source=source,
                url=bundle.final_url,
                confidence=0.7,
                raw_value=found[email],
            )
        )

    # Sort contacts by priority so the most relevant mailbox is first (deterministic).
    lead.contacts.sort(key=lambda c: (-_classify(c.email)[1], c.email))

    # Record contact-page links for completeness.
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if "contact" in text or "contact" in a["href"].lower():
            evidence.append(
                FieldValue(
                    field="contact_page",
                    value=a["href"],
                    source=source,
                    url=bundle.final_url,
                    confidence=0.5,
                )
            )
            break

    return evidence


def href_is_mailto(raw: str) -> bool:
    return raw.lower().startswith("mailto:")
