"""Tests for lead scoring module — written before implementation (TDD)."""

from scoring import normalize_city, classify_role, is_target_type, score_lead, recommend


# --- normalize_city ---

class TestNormalizeCity:
    def test_chihuahua_variants(self):
        assert normalize_city("Chihuahua, Chih.") == "chihuahua"
        assert normalize_city("CHIHUAHUA") == "chihuahua"
        assert normalize_city("  chihuahua ") == "chihuahua"
        assert normalize_city("Chihuahua, Chih") == "chihuahua"

    def test_juarez_variants(self):
        assert normalize_city("Juárez, Chih.") == "juarez"
        assert normalize_city("Ciudad Juárez") == "juarez"
        assert normalize_city("Cd. Juárez") == "juarez"
        assert normalize_city("CD JUAREZ") == "juarez"
        assert normalize_city("Cd. Juárez, Chih.") == "juarez"

    def test_other_city(self):
        assert normalize_city("Monterrey") == "monterrey"
        assert normalize_city("CDMX") == "cdmx"

    def test_empty_and_none(self):
        assert normalize_city("") == ""
        assert normalize_city(None) == ""


# --- classify_role ---

class TestClassifyRole:
    def test_gm_roles(self):
        assert classify_role("Director General") == "GM"
        assert classify_role("Gerente General") == "GM"
        assert classify_role("CEO") == "GM"

    def test_hr_roles(self):
        assert classify_role("Director de Recursos Humanos") == "HR"
        assert classify_role("Gerente de RH") == "HR"
        assert classify_role("Jefe de Capital Humano") == "HR"

    def test_ops_roles(self):
        assert classify_role("Director de Operaciones") == "OPS"
        assert classify_role("Gerente de Planta") == "OPS"
        assert classify_role("COO") == "OPS"

    def test_unknown(self):
        assert classify_role("Contador") == "OTHER"
        assert classify_role("") == "OTHER"
        assert classify_role(None) == "OTHER"


# --- is_target_type ---

class TestIsTargetType:
    def test_target_types(self):
        assert is_target_type("Empresa de servicio") is True
        assert is_target_type("Empresa comercial") is True
        assert is_target_type("Industria alimentaria") is True
        assert is_target_type("Cadena de tiendas") is True
        assert is_target_type("Industria automotriz") is True
        assert is_target_type("Industria metalmecánica") is True

    def test_non_target(self):
        assert is_target_type("Gobierno") is False
        assert is_target_type("Escuela") is False

    def test_case_insensitive(self):
        assert is_target_type("EMPRESA DE SERVICIO") is True
        assert is_target_type("industria alimentaria") is True

    def test_empty(self):
        assert is_target_type("") is False
        assert is_target_type(None) is False


# --- score_lead ---

class TestScoreLead:
    def test_perfect_lead(self):
        lead = {
            "city": "Chihuahua, Chih.",
            "role": "Director General",
            "company_type": "Industria alimentaria",
            "size": "AAA",
            "has_email": True,
        }
        s = score_lead(lead)
        assert s >= 80

    def test_non_local_lead(self):
        lead = {
            "city": "Monterrey",
            "role": "Director General",
            "company_type": "Industria alimentaria",
            "size": "AAA",
            "has_email": True,
        }
        s = score_lead(lead)
        # Non-local leads max out at 60 (role+type+size) — below recommend threshold
        assert s <= 60

    def test_no_email_penalty(self):
        lead = {
            "city": "Chihuahua, Chih.",
            "role": "Director General",
            "company_type": "Industria alimentaria",
            "size": "AAA",
            "has_email": False,
        }
        s = score_lead(lead)
        assert s == 0  # no email = not contactable

    def test_small_size_lower(self):
        big = score_lead({
            "city": "Juárez, Chih.",
            "role": "Gerente de RH",
            "company_type": "Empresa comercial",
            "size": "AAA",
            "has_email": True,
        })
        small = score_lead({
            "city": "Juárez, Chih.",
            "role": "Gerente de RH",
            "company_type": "Empresa comercial",
            "size": "B",
            "has_email": True,
        })
        assert big > small

    def test_score_is_int_0_to_100(self):
        s = score_lead({
            "city": "Chihuahua",
            "role": "CEO",
            "company_type": "Industria",
            "size": "A",
            "has_email": True,
        })
        assert isinstance(s, int)
        assert 0 <= s <= 100


# --- recommend ---

class TestRecommend:
    def test_high_score_recommended(self):
        lead = {
            "city": "Chihuahua, Chih.",
            "role": "Director General",
            "company_type": "Industria alimentaria",
            "size": "AAA",
            "has_email": True,
        }
        assert recommend(lead) is True

    def test_non_local_not_recommended(self):
        lead = {
            "city": "Monterrey",
            "role": "Director General",
            "company_type": "Industria alimentaria",
            "size": "AAA",
            "has_email": True,
        }
        assert recommend(lead) is False

    def test_no_email_not_recommended(self):
        lead = {
            "city": "Juárez, Chih.",
            "role": "CEO",
            "company_type": "Empresa de servicio",
            "size": "AA",
            "has_email": False,
        }
        assert recommend(lead) is False

    def test_other_role_not_recommended_even_if_local_and_large(self):
        lead = {
            "city": "Chihuahua, Chih.",
            "role": "Gerente de Compras",
            "company_type": "Empresa comercial",
            "size": "AA",
            "has_email": True,
        }
        assert recommend(lead) is False
