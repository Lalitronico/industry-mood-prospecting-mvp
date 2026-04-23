"""Tests for draft generation module — written before implementation (TDD)."""

from drafts import FOLLOW_UP_TEMPLATES, TEMPLATES, generate_draft


# --- Helper lead fixtures ---

def _gm_lead():
    return {
        "company": "Aceros del Norte, S.A. de C.V.",
        "contact_name": "Lic. Roberto Hernández",
        "role": "Director General",
        "email": "rhernandez@acerosnorte.com",
        "company_type": "Industria metalmecánica",
        "size": "AAA",
        "city": "Chihuahua, Chih.",
        "score": 100,
        "recommended": True,
    }


def _hr_lead():
    return {
        "company": "Grupo Comercial Río Bravo",
        "contact_name": "María López",
        "role": "Gerente de Recursos Humanos",
        "email": "mlopez@riobravo.mx",
        "company_type": "Empresa comercial",
        "size": "AA",
        "city": "Juárez, Chih.",
        "score": 95,
        "recommended": True,
    }


def _ops_lead():
    return {
        "company": "Alimentos del Valle",
        "contact_name": "Ing. Carlos Mendoza",
        "role": "Gerente de Operaciones",
        "email": "cmendoza@alvalle.com",
        "company_type": "Industria alimentaria",
        "size": "A",
        "city": "Chihuahua, Chih.",
        "score": 85,
        "recommended": True,
    }


# --- Templates exist for each role ---

class TestTemplatesExist:
    def test_gm_template(self):
        assert "GM" in TEMPLATES

    def test_hr_template(self):
        assert "HR" in TEMPLATES

    def test_ops_template(self):
        assert "OPS" in TEMPLATES

    def test_each_template_has_subject_and_body(self):
        for role, tpl in TEMPLATES.items():
            assert "subject" in tpl, f"Missing subject for {role}"
            assert "body" in tpl, f"Missing body for {role}"

    def test_follow_up_templates_exist_for_steps_two_and_three(self):
        assert set(FOLLOW_UP_TEMPLATES) == {2, 3}
        for step_templates in FOLLOW_UP_TEMPLATES.values():
            assert {"GM", "HR", "OPS"}.issubset(step_templates)


# --- generate_draft returns correct structure ---

class TestGenerateDraftStructure:
    def test_returns_dict(self):
        result = generate_draft(_gm_lead())
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = generate_draft(_gm_lead())
        for key in ("subject", "body_text", "template_key", "role_bucket",
                     "company", "email", "contact_name"):
            assert key in result, f"Missing key: {key}"

    def test_subject_is_nonempty_string(self):
        result = generate_draft(_gm_lead())
        assert isinstance(result["subject"], str)
        assert len(result["subject"]) > 0

    def test_body_text_is_nonempty_string(self):
        result = generate_draft(_gm_lead())
        assert isinstance(result["body_text"], str)
        assert len(result["body_text"]) > 10


# --- Role-aware template selection ---

class TestRoleAwareTemplates:
    def test_gm_gets_gm_template(self):
        result = generate_draft(_gm_lead())
        assert result["role_bucket"] == "GM"
        assert result["template_key"] == "GM"

    def test_hr_gets_hr_template(self):
        result = generate_draft(_hr_lead())
        assert result["role_bucket"] == "HR"
        assert result["template_key"] == "HR"

    def test_ops_gets_ops_template(self):
        result = generate_draft(_ops_lead())
        assert result["role_bucket"] == "OPS"
        assert result["template_key"] == "OPS"


# --- Personalization ---

class TestPersonalization:
    def test_body_contains_company_name(self):
        lead = _gm_lead()
        result = generate_draft(lead)
        assert lead["company"] in result["body_text"]

    def test_body_contains_city(self):
        lead = _hr_lead()
        result = generate_draft(lead)
        # City should appear somewhere (possibly cleaned up)
        assert "Juárez" in result["body_text"] or "Juarez" in result["body_text"]

    def test_body_contains_company_type(self):
        lead = _ops_lead()
        result = generate_draft(lead)
        assert lead["company_type"].lower() in result["body_text"].lower()

    def test_subject_contains_company_name(self):
        lead = _gm_lead()
        result = generate_draft(lead)
        assert lead["company"] in result["subject"]

    def test_metadata_carries_through(self):
        lead = _gm_lead()
        result = generate_draft(lead)
        assert result["company"] == lead["company"]
        assert result["email"] == lead["email"]
        assert result["contact_name"] == lead["contact_name"]

    def test_step_metadata_defaults_to_initial_step(self):
        result = generate_draft(_gm_lead())
        assert result["step_number"] == 1
        assert result["campaign_name"] == "first_wave_local"

    def test_generates_step_two_follow_up(self):
        result = generate_draft(_hr_lead(), step_number=2)
        assert result["step_number"] == 2
        assert "Seguimiento" in result["subject"]

    def test_generates_step_three_close_loop(self):
        result = generate_draft(_ops_lead(), step_number=3)
        assert result["step_number"] == 3
        assert "Cierro" in result["subject"]

    def test_invalid_step_raises(self):
        import pytest

        with pytest.raises(ValueError):
            generate_draft(_gm_lead(), step_number=4)


# --- Spanish copy ---

class TestSpanishCopy:
    def test_body_is_in_spanish(self):
        """Check for at least a few common Spanish words in the body."""
        result = generate_draft(_gm_lead())
        body = result["body_text"].lower()
        spanish_words = ["empresa", "equipo", "encuesta", "clima", "minutos",
                         "conversación", "conversacion", "plática", "platica"]
        assert any(w in body for w in spanish_words), \
            f"Body doesn't seem to be in Spanish: {body[:200]}"

    def test_subject_is_in_spanish(self):
        result = generate_draft(_hr_lead())
        subject = result["subject"].lower()
        spanish_words = ["clima", "equipo", "empresa", "encuesta", "pulso"]
        assert any(w in subject for w in spanish_words), \
            f"Subject doesn't seem to be in Spanish: {subject}"


# --- Tone: no hype words ---

class TestTone:
    def test_no_hype_words(self):
        """Drafts should be free of aggressive sales language."""
        hype = ["revolucionar", "increíble", "increible", "garantiz",
                "oferta", "descuento", "gratis", "sin costo",
                "exclusiv", "no te pierdas", "oportunidad única"]
        for lead_fn in (_gm_lead, _hr_lead, _ops_lead):
            result = generate_draft(lead_fn())
            text = (result["subject"] + " " + result["body_text"]).lower()
            for word in hype:
                assert word not in text, \
                    f"Found hype word '{word}' in draft for {lead_fn.__name__}"
