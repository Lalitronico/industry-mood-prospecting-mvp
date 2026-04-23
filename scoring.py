"""Lead scoring for Industry Mood prospecting — pure functions, stdlib only.

Designed around the Excel profiling of 'Empresarial AAA AA A y B.xlsx':
- 15,615 total company rows
- 189 exact local rows (Chihuahua + Juárez), all with email
- 172 local rows size A/AA/AAA
- Priority roles: GM 34, HR 28, OPS 16
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Constants derived from Excel profiling
# ---------------------------------------------------------------------------

LOCAL_CITIES = {"chihuahua", "juarez"}

TARGET_TYPES = {
    "empresa de servicio",
    "empresa comercial",
    "industria alimentaria",
    "cadena de tiendas",
    "industria automotriz",
    "industria del papel",
    "industria de materiales de construcción",
    "industria de materiales de construccion",
    "industria extractiva",
    "industria",
    "industria química",
    "industria quimica",
    "industria metalmecánica",
    "industria metalmecanica",
}

SIZE_POINTS = {"AAA": 20, "AA": 15, "A": 10, "B": 5}
PRIORITY_SIZES = {"AAA", "AA", "A"}

ROLE_PATTERNS = {
    "GM": re.compile(
        r"director\s*general|gerente\s*general|ceo|presidente|dueño|propietario",
        re.IGNORECASE,
    ),
    "HR": re.compile(
        r"recursos\s*humanos|capital\s*humano|\brh\b|\bhr\b|talento|people",
        re.IGNORECASE,
    ),
    "OPS": re.compile(
        r"operaciones|planta|manufactura|producción|produccion|\bcoo\b|supply\s*chain",
        re.IGNORECASE,
    ),
}

ROLE_POINTS = {"GM": 20, "HR": 20, "OPS": 15, "OTHER": 0}

RECOMMEND_THRESHOLD = 65


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_accents(s: str) -> str:
    """Remove Unicode accents so 'Juárez' becomes 'Juarez'."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_city(raw: str | None) -> str:
    """Return a canonical city key: lowercase, no accents, no state suffix."""
    if not raw:
        return ""
    cleaned = _strip_accents(raw.strip()).lower()
    # Strip state suffixes like ", Chih." or ", Chih"
    cleaned = re.sub(r",\s*chih\.?$", "", cleaned)
    # Handle "Ciudad Juárez" / "Cd. Juárez" variants (require word boundary after cd.)
    cleaned = re.sub(r"^(ciudad\s+|cd\.?\s+)", "", cleaned)
    cleaned = cleaned.strip()
    return cleaned


def classify_role(title: str | None) -> str:
    """Classify a job title into GM, HR, OPS, or OTHER."""
    if not title:
        return "OTHER"
    for role, pattern in ROLE_PATTERNS.items():
        if pattern.search(title):
            return role
    return "OTHER"


def is_target_type(company_type: str | None) -> bool:
    """Return True if the company type is in the target set."""
    if not company_type:
        return False
    normalized = _strip_accents(company_type.strip()).lower()
    return normalized in TARGET_TYPES


def score_lead(lead: dict) -> int:
    """Score a lead 0-100 based on geography, role, type, and size.

    Expected keys: city, role, company_type, size, has_email.
    """
    if not lead.get("has_email"):
        return 0

    points = 0

    # Geography (40 points max)
    city = normalize_city(lead.get("city"))
    if city in LOCAL_CITIES:
        points += 40

    # Role (20 points max)
    role = classify_role(lead.get("role"))
    points += ROLE_POINTS.get(role, 0)

    # Company type (20 points max)
    if is_target_type(lead.get("company_type")):
        points += 20

    # Size (20 points max)
    size = (lead.get("size") or "").upper().strip()
    points += SIZE_POINTS.get(size, 0)

    return min(points, 100)


def recommend(lead: dict) -> bool:
    """Return True if the lead should be in the first-wave outreach shortlist.

    First wave is intentionally restricted to local leads with priority roles
    (GM/HR/OPS), target company types, and A+ company sizes. Other local leads
    can remain in the imported dataset but should not be pushed into the initial
    outreach batch.
    """
    if not lead.get("has_email"):
        return False
    if normalize_city(lead.get("city")) not in LOCAL_CITIES:
        return False
    if classify_role(lead.get("role")) == "OTHER":
        return False
    if not is_target_type(lead.get("company_type")):
        return False
    if (lead.get("size") or "").upper().strip() not in PRIORITY_SIZES:
        return False
    return score_lead(lead) >= RECOMMEND_THRESHOLD
