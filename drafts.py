"""Template-driven draft generation for Industry Mood outreach — stdlib only.

Generates role-aware email drafts in Spanish from lead dicts.
Designed so a future LLM layer can replace generate_draft() without
touching the rest of the pipeline.
"""

from scoring import classify_role

# ---------------------------------------------------------------------------
# Templates — keyed by role bucket (GM / HR / OPS)
# Placeholders: {company}, {company_type}, {city}, {contact_name}, {size_line}
# ---------------------------------------------------------------------------

TEMPLATES = {
    "GM": {
        "subject": "Clima laboral en {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "Le escribo brevemente porque en Industry Mood trabajamos con "
            "empresas del sector {company_type} en {city} — como {company} — y creemos que "
            "una encuesta de clima laboral rápida podría darle visibilidad "
            "sobre cómo se siente su equipo hoy.{size_line}\n\n"
            "Es un pulso de 5 minutos para sus colaboradores, con resultados "
            "claros y accionables.\n\n"
            "¿Tendría 15 minutos esta semana para una plática breve sobre "
            "cómo funciona?\n\n"
            "Quedo atento,\n"
            "— Industry Mood"
        ),
    },
    "HR": {
        "subject": "Encuesta de pulso para el equipo de {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "Sé que medir el clima laboral de manera ágil es uno de los retos "
            "constantes en Recursos Humanos. En Industry Mood ayudamos a empresas "
            "del sector {company_type} en {city} a tener un diagnóstico rápido "
            "del ánimo de sus equipos.{size_line}\n\n"
            "La encuesta toma 5 minutos por persona y entrega resultados "
            "listos para actuar.\n\n"
            "¿Le parece si agendamos 15 minutos para mostrarle cómo funciona?\n\n"
            "Saludos cordiales,\n"
            "— Industry Mood"
        ),
    },
    "OPS": {
        "subject": "Clima laboral en operaciones — {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "En áreas de operaciones, la rotación y el clima laboral impactan "
            "directamente la productividad. En Industry Mood ayudamos a empresas "
            "del sector {company_type} en {city} a medir el pulso de sus "
            "equipos operativos de forma rápida.{size_line}\n\n"
            "Es una encuesta de 5 minutos que entrega métricas claras sobre "
            "el estado de ánimo del equipo.\n\n"
            "¿Tendría 15 minutos para una conversación breve?\n\n"
            "Saludos,\n"
            "— Industry Mood"
        ),
    },
}

# ---------------------------------------------------------------------------
# Size descriptions for optional personalization
# ---------------------------------------------------------------------------

_SIZE_DESC = {
    "AAA": "Con una operación del tamaño de la suya",
    "AA": "Para una empresa de su escala",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_draft(lead: dict) -> dict:
    """Generate an outreach draft from a lead dict.

    Returns a dict with: subject, body_text, template_key, role_bucket,
    company, email, contact_name.

    The lead dict is expected to have at least: company, contact_name, role,
    email, company_type, city.  Optional: size.
    """
    role_bucket = classify_role(lead.get("role"))
    if role_bucket == "OTHER":
        role_bucket = "GM"  # fallback to GM template

    template = TEMPLATES[role_bucket]

    # Build size line (optional extra sentence)
    size = (lead.get("size") or "").upper().strip()
    size_line = ""
    if size in _SIZE_DESC:
        size_line = f" {_SIZE_DESC[size]}, el impacto es aún más visible."

    # Clean city for display (keep original, just strip whitespace)
    city = (lead.get("city") or "la región").strip()

    placeholders = {
        "company": lead.get("company", ""),
        "company_type": (lead.get("company_type") or "su industria").strip().lower(),
        "city": city,
        "contact_name": lead.get("contact_name", ""),
        "size_line": size_line,
    }

    return {
        "subject": template["subject"].format(**placeholders),
        "body_text": template["body"].format(**placeholders),
        "template_key": role_bucket,
        "role_bucket": role_bucket,
        "company": lead.get("company", ""),
        "email": lead.get("email", ""),
        "contact_name": lead.get("contact_name", ""),
    }
