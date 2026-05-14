"""Template-driven draft generation for Industry Mood outreach.

Generates role-aware Spanish email drafts from lead dicts.
Designed so a future LLM layer can replace generate_draft() without touching
the rest of the pipeline.
"""

from scoring import classify_role


COMPLIANCE_FOOTER = (
    "\n\n---\n"
    "Industry Mood | Ciudad Juárez, Chihuahua, México\n"
    "Si no desea recibir más mensajes de Industry Mood, responda a este correo "
    "con la palabra 'remover' y lo retiraremos de la lista."
)


TEMPLATES = {
    "GM": {
        "subject": "¿Cómo está el ánimo del equipo en {company_short}?",
        "body": (
            "Hola,\n\n"
            "Soy Eduardo Vera de Industry Mood. Trabajamos con organizaciones de "
            "{company_type} en {city} midiendo clima laboral con pulsos cortos, "
            "no con encuestas anuales largas.\n\n"
            "Una pregunta concreta: ¿hoy tienen forma de saber, en menos de una "
            "semana, si el ánimo del equipo cambió o si hay señales tempranas de "
            "rotación y desgaste?\n\n"
            "Si le interesa, le mando un ejemplo breve del reporte que entregamos "
            "para que lo revise sin compromiso. ¿Le sirve?\n\n"
            "Eduardo Vera\n"
            "Industry Mood\n"
            "admin@industrymood.com\n\n"
            "Si prefiere no recibir más correos, responda \"baja\" y lo retiro de la lista."
        ),
    },
    "HR": {
        "subject": "Pulso de clima laboral para {company_short}",
        "body": (
            "Hola,\n\n"
            "Soy Eduardo Vera de Industry Mood. Ayudamos a equipos de Recursos "
            "Humanos en organizaciones de {company_type} en {city} a medir clima "
            "laboral con una encuesta breve y resultados listos para revisar.\n\n"
            "La idea es detectar señales de ánimo, rotación o desgaste antes de "
            "que se conviertan en problemas más caros de atender.\n\n"
            "Si le interesa, le mando un ejemplo breve del reporte que entregamos "
            "para que lo revise sin compromiso. ¿Le sirve?\n\n"
            "Eduardo Vera\n"
            "Industry Mood\n"
            "admin@industrymood.com\n\n"
            "Si prefiere no recibir más correos, responda \"baja\" y lo retiro de la lista."
        ),
    },
    "OPS": {
        "subject": "Pulso de clima en operaciones - {company_short}",
        "body": (
            "Hola,\n\n"
            "Soy Eduardo Vera de Industry Mood. En operaciones, el clima laboral "
            "termina impactando rotación, ausentismo y productividad. Trabajamos "
            "con organizaciones de {company_type} en {city} para medir ese pulso "
            "sin cargar al equipo con procesos largos.\n\n"
            "Si le interesa, le mando un ejemplo breve del reporte que entregamos "
            "para que lo revise sin compromiso. ¿Le sirve?\n\n"
            "Eduardo Vera\n"
            "Industry Mood\n"
            "admin@industrymood.com\n\n"
            "Si prefiere no recibir más correos, responda \"baja\" y lo retiro de la lista."
        ),
    },
}


FOLLOW_UP_TEMPLATES = {
    2: {
        "GM": {
            "subject": "Seguimiento sobre clima laboral en {company}",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Le doy seguimiento a mi mensaje anterior sobre Industry Mood. "
                "La idea es sencilla: ayudarle a tener una lectura rapida del clima "
                "laboral antes de que problemas como rotacion, desgaste o desalineacion "
                "se vuelvan mas costosos.\n\n"
                "Si tiene sentido, puedo mostrarle en 15 minutos como se veria un "
                "pulso para {company}.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
        "HR": {
            "subject": "Seguimiento - encuesta de pulso para {company}",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Le escribo solo para dar seguimiento. Industry Mood puede servir como "
                "una herramienta ligera para medir clima laboral y detectar focos de "
                "atencion sin cargar al equipo de RH con procesos largos.\n\n"
                "Si le parece util, podemos revisarlo en una llamada breve de 15 minutos.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
        "OPS": {
            "subject": "Seguimiento sobre clima en operaciones",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Retomo mi mensaje anterior. En equipos operativos, una medicion corta "
                "de clima puede ayudar a anticipar fricciones que terminan afectando "
                "rotacion, ausentismo o productividad.\n\n"
                "Si le interesa, puedo mostrarle en 15 minutos como funcionaria para {company}.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
    },
    3: {
        "GM": {
            "subject": "Cierro el ciclo - {company}",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Cierro el ciclo para no insistir de mas. Si en este momento medir clima "
                "laboral no es prioridad para {company}, lo entiendo perfectamente.\n\n"
                "Si mas adelante quieren explorar una encuesta de pulso rapida para "
                "identificar riesgos de rotacion o desgaste, con gusto retomamos.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
        "HR": {
            "subject": "Cierro el ciclo - pulso de clima",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Cierro el ciclo para no llenar su bandeja. Si ahora no es buen momento "
                "para revisar Industry Mood, no hay problema.\n\n"
                "Cuando quieran medir clima laboral con una encuesta breve y resultados "
                "accionables, con gusto lo retomamos.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
        "OPS": {
            "subject": "Cierro el ciclo - operaciones",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Cierro el ciclo para no insistir de mas. Si ahora no es prioridad "
                "medir clima en operaciones, lo entiendo.\n\n"
                "Si en otro momento quieren anticipar riesgos de rotacion, desgaste o "
                "fricciones del equipo operativo con un pulso corto, con gusto retomamos.\n\n"
                "Saludos,\n"
                "Industry Mood"
            ),
        },
    },
}


_SIZE_DESC = {
    "AAA": "Con una operacion del tamano de la suya",
    "AA": "Para una empresa de su escala",
}


def _role_bucket(lead: dict) -> str:
    role_bucket = lead.get("role_bucket") or classify_role(lead.get("role"))
    return role_bucket if role_bucket in TEMPLATES else "GM"


def _clean_company_name(company: str) -> str:
    """Return a human-readable company name without legal suffixes."""
    cleaned = (company or "").strip()
    suffixes = [
        ", S.A. DE C.V.",
        ", S.A.B. DE C.V.",
        ", S. DE R.L. DE C.V.",
        ", S. DE R.L.",
        ", A.C.",
        ", S.A.",
        " S.A. DE C.V.",
        " S.A.B. DE C.V.",
        " S. DE R.L. DE C.V.",
        " S. DE R.L.",
        " A.C.",
        " S.A.",
    ]
    upper = cleaned.upper()
    for suffix in suffixes:
        if upper.endswith(suffix):
            return cleaned[: -len(suffix)].strip(" ,")
    return cleaned


def generate_draft(lead: dict, step_number: int = 1) -> dict:
    """Generate an outreach draft from a lead dict.

    Returns a dict with subject, body_text, role/campaign metadata, and contact
    fields. step_number supports the 3-step sequence: 1 initial, 2 follow-up,
    3 final close-the-loop message.
    """
    role_bucket = _role_bucket(lead)

    if step_number == 1:
        template = TEMPLATES[role_bucket]
    elif step_number in FOLLOW_UP_TEMPLATES:
        template = FOLLOW_UP_TEMPLATES[step_number][role_bucket]
    else:
        raise ValueError("step_number must be 1, 2, or 3")

    size = (lead.get("size") or "").upper().strip()
    size_line = ""
    if size in _SIZE_DESC:
        size_line = f" {_SIZE_DESC[size]}, el impacto es aun mas visible."

    city = (lead.get("city") or "la región").strip()
    company = lead.get("company", "")
    placeholders = {
        "company": company,
        "company_short": _clean_company_name(company),
        "company_type": (lead.get("company_type") or "su industria").strip().lower(),
        "city": city,
        "contact_name": lead.get("contact_name", ""),
        "size_line": size_line,
    }

    email = lead.get("email", "")
    return {
        "subject": template["subject"].format(**placeholders),
        "body_text": template["body"].format(**placeholders) + COMPLIANCE_FOOTER,
        "template_key": role_bucket,
        "role_bucket": role_bucket,
        "company": lead.get("company", ""),
        "email": email,
        "contact_name": lead.get("contact_name", ""),
        "campaign_name": lead.get("campaign_name", "first_wave_local"),
        "step_number": step_number,
        "lead_key": (lead.get("lead_key") or email).lower(),
    }
