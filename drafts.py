"""Template-driven draft generation for Industry Mood outreach.

Generates role-aware Spanish email drafts from lead dicts.
Designed so a future LLM layer can replace generate_draft() without touching
the rest of the pipeline.
"""

from scoring import classify_role


TEMPLATES = {
    "GM": {
        "subject": "Clima laboral en {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "Le escribo brevemente porque en Industry Mood trabajamos con "
            "empresas del sector {company_type} en {city}, como {company}, y creemos que "
            "una encuesta de clima laboral rapida podria darle visibilidad "
            "sobre como se siente su equipo hoy.{size_line}\n\n"
            "Es un pulso de 5 minutos para sus colaboradores, con resultados "
            "claros y accionables.\n\n"
            "Tendria 15 minutos esta semana para una platica breve sobre "
            "como funciona?\n\n"
            "Quedo atento,\n"
            "Industry Mood"
        ),
    },
    "HR": {
        "subject": "Encuesta de pulso para el equipo de {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "Se que medir el clima laboral de manera agil es uno de los retos "
            "constantes en Recursos Humanos. En Industry Mood ayudamos a empresas "
            "del sector {company_type} en {city} a tener un diagnostico rapido "
            "del animo de sus equipos.{size_line}\n\n"
            "La encuesta toma 5 minutos por persona y entrega resultados "
            "listos para actuar.\n\n"
            "Le parece si agendamos 15 minutos para mostrarle como funciona?\n\n"
            "Saludos cordiales,\n"
            "Industry Mood"
        ),
    },
    "OPS": {
        "subject": "Clima laboral en operaciones - {company}",
        "body": (
            "Estimado/a {contact_name},\n\n"
            "En areas de operaciones, la rotacion y el clima laboral impactan "
            "directamente la productividad. En Industry Mood ayudamos a empresas "
            "del sector {company_type} en {city} a medir el pulso de sus "
            "equipos operativos de forma rapida.{size_line}\n\n"
            "Es una encuesta de 5 minutos que entrega metricas claras sobre "
            "el estado de animo del equipo.\n\n"
            "Tendria 15 minutos para una conversacion breve?\n\n"
            "Saludos,\n"
            "Industry Mood"
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

    city = (lead.get("city") or "la region").strip()
    placeholders = {
        "company": lead.get("company", ""),
        "company_type": (lead.get("company_type") or "su industria").strip().lower(),
        "city": city,
        "contact_name": lead.get("contact_name", ""),
        "size_line": size_line,
    }

    email = lead.get("email", "")
    return {
        "subject": template["subject"].format(**placeholders),
        "body_text": template["body"].format(**placeholders),
        "template_key": role_bucket,
        "role_bucket": role_bucket,
        "company": lead.get("company", ""),
        "email": email,
        "contact_name": lead.get("contact_name", ""),
        "campaign_name": lead.get("campaign_name", "first_wave_local"),
        "step_number": step_number,
        "lead_key": (lead.get("lead_key") or email).lower(),
    }
