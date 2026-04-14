"""Tests for Excel importer module — written before implementation (TDD).

Tests cover:
- xlsx parsing helpers (shared strings, cell values)
- column mapping from raw row to lead dict
- deduplication by (company, email)
- full pipeline: parse → map → score → dedupe → recommend
"""

import os
import tempfile
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

# We'll import from the module we're about to create
from importer import (
    parse_shared_strings,
    iter_sheet_rows,
    map_row_to_lead,
    deduplicate_leads,
    import_leads,
    COLUMN_MAP,
)


# ---------------------------------------------------------------------------
# Helpers to build minimal .xlsx files for testing
# ---------------------------------------------------------------------------

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
WB_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _make_test_xlsx(rows, shared_strings=None, sheet_name="EMPRESARIAL"):
    """Create a minimal .xlsx in a temp file. Returns the path.

    rows: list of list-of-(col_letter, value) tuples per row.
          Values that are strings get added to shared strings automatically
          unless shared_strings is provided explicitly.
    """
    # Build shared strings from row values if not given
    if shared_strings is None:
        seen = {}
        ss_list = []
        for row in rows:
            for _col, val in row:
                if isinstance(val, str) and val not in seen:
                    seen[val] = len(ss_list)
                    ss_list.append(val)
        shared_strings = ss_list

    ss_index = {s: i for i, s in enumerate(shared_strings)}

    # -- sharedStrings.xml --
    ssi_root = Element("sst", xmlns=SHEET_NS)
    for s in shared_strings:
        si = SubElement(ssi_root, "si")
        t = SubElement(si, "t")
        t.text = s

    # -- sheet1.xml --
    ws = Element("worksheet", xmlns=SHEET_NS)
    sd = SubElement(ws, "sheetData")
    for row_idx, cells in enumerate(rows, start=1):
        row_el = SubElement(sd, "row", r=str(row_idx))
        for col, val in cells:
            ref = f"{col}{row_idx}"
            if isinstance(val, str):
                c = SubElement(row_el, "c", r=ref, t="s")
                v = SubElement(c, "v")
                v.text = str(ss_index[val])
            elif val is None:
                # empty cell — skip
                pass
            else:
                c = SubElement(row_el, "c", r=ref)
                v = SubElement(c, "v")
                v.text = str(val)

    # -- workbook.xml --
    wb = Element("workbook", xmlns=WB_NS)
    sheets = SubElement(wb, "sheets")
    SubElement(sheets, "sheet", name=sheet_name, sheetId="1",
               **{f"{{{REL_NS}}}id": "rId1"})

    # -- workbook.xml.rels --
    rels = Element("Relationships", xmlns=RELS_NS)
    SubElement(rels, "Relationship", Id="rId1",
               Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
               Target="worksheets/sheet1.xml")

    # -- [Content_Types].xml --
    ct = Element("Types", xmlns=CT_NS)
    SubElement(ct, "Default", Extension="xml",
               ContentType="application/xml")
    SubElement(ct, "Default", Extension="rels",
               ContentType="application/vnd.openxmlformats-package.relationships+xml")

    # -- write zip --
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("xl/sharedStrings.xml", tostring(ssi_root, xml_declaration=True, encoding="unicode"))
        zf.writestr("xl/worksheets/sheet1.xml", tostring(ws, xml_declaration=True, encoding="unicode"))
        zf.writestr("xl/workbook.xml", tostring(wb, xml_declaration=True, encoding="unicode"))
        zf.writestr("xl/_rels/workbook.xml.rels", tostring(rels, xml_declaration=True, encoding="unicode"))
        zf.writestr("[Content_Types].xml", tostring(ct, xml_declaration=True, encoding="unicode"))
    return path


# Standard header row matching real file
HEADER = [
    ("A", "Compañía"), ("B", "Puesto"), ("C", "Nombre"), ("D", "Email"),
    ("E", "Tipo"), ("F", "Tamaño"), ("G", "personal"), ("H", "Colonia"),
    ("I", "Código postal"), ("J", "Ciudad"),
]


# ---------------------------------------------------------------------------
# parse_shared_strings
# ---------------------------------------------------------------------------

class TestParseSharedStrings:
    def test_basic(self):
        path = _make_test_xlsx([HEADER])
        strings = parse_shared_strings(path)
        assert "Compañía" in strings
        assert "Puesto" in strings
        os.unlink(path)


# ---------------------------------------------------------------------------
# iter_sheet_rows
# ---------------------------------------------------------------------------

class TestIterSheetRows:
    def test_yields_rows(self):
        data_row = [
            ("A", "ACME SA"), ("B", "Director General"), ("C", "Juan"),
            ("D", "juan@acme.com"), ("E", "Industria alimentaria"),
            ("F", "AAA"), ("G", "~500"), ("H", "Centro"),
            ("I", "31000"), ("J", "Chihuahua, Chih."),
        ]
        path = _make_test_xlsx([HEADER, data_row])
        rows = list(iter_sheet_rows(path))
        assert len(rows) == 2  # header + 1 data row
        # First row should be the header values
        assert rows[0]["A"] == "Compañía"
        assert rows[1]["A"] == "ACME SA"
        os.unlink(path)

    def test_empty_sheet(self):
        path = _make_test_xlsx([HEADER])
        rows = list(iter_sheet_rows(path))
        assert len(rows) == 1  # only header
        os.unlink(path)


# ---------------------------------------------------------------------------
# map_row_to_lead
# ---------------------------------------------------------------------------

class TestMapRowToLead:
    def test_basic_mapping(self):
        raw = {
            "A": "ACME SA DE CV",
            "B": "Director General",
            "C": "Sr. Juan Pérez",
            "D": "juan@acme.com",
            "E": "Industria alimentaria",
            "F": "AAA",
            "G": "~500",
            "J": "Chihuahua, Chih.",
        }
        lead = map_row_to_lead(raw)
        assert lead["company"] == "ACME SA DE CV"
        assert lead["role"] == "Director General"
        assert lead["contact_name"] == "Sr. Juan Pérez"
        assert lead["email"] == "juan@acme.com"
        assert lead["company_type"] == "Industria alimentaria"
        assert lead["size"] == "AAA"
        assert lead["city"] == "Chihuahua, Chih."
        assert lead["has_email"] is True

    def test_missing_email(self):
        raw = {"A": "ACME SA", "B": "CEO", "J": "Juárez"}
        lead = map_row_to_lead(raw)
        assert lead["has_email"] is False
        assert lead["email"] == ""

    def test_strips_whitespace(self):
        raw = {"A": "  ACME  ", "D": " x@y.com ", "J": " Juárez "}
        lead = map_row_to_lead(raw)
        assert lead["company"] == "ACME"
        assert lead["email"] == "x@y.com"

    def test_empty_row_returns_lead_with_defaults(self):
        lead = map_row_to_lead({})
        assert lead["company"] == ""
        assert lead["has_email"] is False


# ---------------------------------------------------------------------------
# deduplicate_leads
# ---------------------------------------------------------------------------

class TestDeduplicateLeads:
    def test_removes_exact_duplicates(self):
        leads = [
            {"company": "ACME", "email": "a@acme.com", "role": "CEO"},
            {"company": "ACME", "email": "a@acme.com", "role": "CEO"},
        ]
        deduped = deduplicate_leads(leads)
        assert len(deduped) == 1

    def test_keeps_different_emails_same_company(self):
        leads = [
            {"company": "ACME", "email": "a@acme.com", "role": "CEO"},
            {"company": "ACME", "email": "b@acme.com", "role": "HR"},
        ]
        deduped = deduplicate_leads(leads)
        assert len(deduped) == 2

    def test_keeps_different_companies_same_email(self):
        leads = [
            {"company": "ACME", "email": "a@x.com"},
            {"company": "BETA", "email": "a@x.com"},
        ]
        deduped = deduplicate_leads(leads)
        assert len(deduped) == 2

    def test_case_insensitive_email(self):
        leads = [
            {"company": "ACME", "email": "A@acme.com"},
            {"company": "ACME", "email": "a@acme.com"},
        ]
        deduped = deduplicate_leads(leads)
        assert len(deduped) == 1

    def test_preserves_first_occurrence(self):
        leads = [
            {"company": "ACME", "email": "a@acme.com", "role": "CEO"},
            {"company": "ACME", "email": "a@acme.com", "role": "HR"},
        ]
        deduped = deduplicate_leads(leads)
        assert deduped[0]["role"] == "CEO"


# ---------------------------------------------------------------------------
# import_leads (integration: parse + map + score + dedupe)
# ---------------------------------------------------------------------------

class TestImportLeads:
    def _make_xlsx_with_leads(self, data_rows):
        return _make_test_xlsx([HEADER] + data_rows)

    def test_full_pipeline(self):
        rows = [
            [("A", "ACME SA"), ("B", "Director General"), ("C", "Juan"),
             ("D", "juan@acme.com"), ("E", "Industria alimentaria"),
             ("F", "AAA"), ("J", "Chihuahua, Chih.")],
        ]
        path = self._make_xlsx_with_leads(rows)
        leads = import_leads(path)
        assert len(leads) == 1
        lead = leads[0]
        assert lead["company"] == "ACME SA"
        assert "score" in lead
        assert "recommended" in lead
        assert lead["score"] >= 80  # local + GM + target type + AAA
        assert lead["recommended"] is True
        os.unlink(path)

    def test_skips_header_row(self):
        rows = [
            [("A", "ACME SA"), ("B", "CEO"), ("C", "Juan"),
             ("D", "j@a.com"), ("E", "Industria"), ("F", "A"),
             ("J", "Chihuahua")],
        ]
        path = self._make_xlsx_with_leads(rows)
        leads = import_leads(path)
        # Should not include a lead where company == "Compañía" (header)
        assert all(l["company"] != "Compañía" for l in leads)
        os.unlink(path)

    def test_deduplicates(self):
        row = [("A", "ACME SA"), ("B", "CEO"), ("C", "Juan"),
               ("D", "j@a.com"), ("E", "Industria"), ("F", "A"),
               ("J", "Chihuahua")]
        path = self._make_xlsx_with_leads([row, row])
        leads = import_leads(path)
        assert len(leads) == 1
        os.unlink(path)

    def test_non_local_lead_scored_low(self):
        rows = [
            [("A", "FAR CO"), ("B", "CEO"), ("C", "Ana"),
             ("D", "a@far.com"), ("E", "Industria"), ("F", "AAA"),
             ("J", "Monterrey")],
        ]
        path = self._make_xlsx_with_leads(rows)
        leads = import_leads(path)
        assert len(leads) == 1
        assert leads[0]["recommended"] is False
        os.unlink(path)

    def test_no_email_excluded_from_results(self):
        """Leads with no email get score 0 — still included but not recommended."""
        rows = [
            [("A", "NO EMAIL CO"), ("B", "CEO"), ("C", "X"),
             ("E", "Industria"), ("F", "AAA"), ("J", "Chihuahua")],
        ]
        path = self._make_xlsx_with_leads(rows)
        leads = import_leads(path)
        assert len(leads) == 1
        assert leads[0]["score"] == 0
        assert leads[0]["recommended"] is False
        os.unlink(path)

    def test_multiple_contacts_same_company(self):
        rows = [
            [("A", "ACME SA"), ("B", "CEO"), ("C", "Juan"),
             ("D", "ceo@acme.com"), ("E", "Industria"), ("F", "AAA"),
             ("J", "Chihuahua")],
            [("A", "ACME SA"), ("B", "Gerente de RH"), ("C", "Ana"),
             ("D", "rh@acme.com"), ("E", "Industria"), ("F", "AAA"),
             ("J", "Chihuahua")],
        ]
        path = self._make_xlsx_with_leads(rows)
        leads = import_leads(path)
        assert len(leads) == 2  # different emails = different contacts
        os.unlink(path)
