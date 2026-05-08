"""Lightweight validation helpers for prospecting data."""

import re

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def has_valid_email_syntax(email: str | None) -> bool:
    """Return True for syntactically plausible business email addresses.

    This intentionally checks syntax only. MX/domain verification can be added
    later before real sending, but this catches obvious bad rows without network
    calls or extra dependencies.
    """
    if not email:
        return False
    cleaned = email.strip()
    if not _EMAIL_RE.match(cleaned):
        return False
    local, domain = cleaned.rsplit("@", 1)
    if local.startswith(".") or local.endswith("."):
        return False
    if ".." in local or ".." in domain:
        return False
    return True
