"""Excel importer for Industry Mood lead file — stdlib only (zipfile + xml).

Reads the EMPRESARIAL sheet from 'Empresarial AAA AA A y B.xlsx',
maps columns to lead dicts, scores them via scoring.py, and deduplicates.
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from scoring import score_lead, recommend

# ---------------------------------------------------------------------------
# Column mapping: Excel column letter → lead dict key
# ---------------------------------------------------------------------------

COLUMN_MAP = {
    "A": "company",
    "B": "role",
    "C": "contact_name",
    "D": "email",
    "E": "company_type",
    "F": "size",
    "G": "employees",
    "H": "colonia",
    "I": "postal_code",
    "J": "city",
    "K": "area_code",
    "M": "phone1",
    "N": "phone2",
    "O": "phone3",
    "P": "email_corp",
    "Q": "website",
}

NS = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

# Regex to extract column letters from cell references like "A1", "AB12"
_COL_RE = re.compile(r"^([A-Z]+)")


# ---------------------------------------------------------------------------
# Low-level xlsx helpers
# ---------------------------------------------------------------------------

def parse_shared_strings(xlsx_path: str) -> list[str]:
    """Extract the shared-strings table from an .xlsx file."""
    with zipfile.ZipFile(xlsx_path) as zf:
        try:
            tree = ET.parse(zf.open("xl/sharedStrings.xml"))
        except KeyError:
            return []

    strings = []
    for si in tree.findall(".//ns:si", NS):
        t = si.find("ns:t", NS)
        if t is not None and t.text is not None:
            strings.append(t.text)
        else:
            # Concatenated rich-text runs
            parts = []
            for r in si.findall("ns:r", NS):
                rt = r.find("ns:t", NS)
                if rt is not None and rt.text is not None:
                    parts.append(rt.text)
            strings.append("".join(parts))
    return strings


def _find_empresarial_sheet(zf: zipfile.ZipFile) -> str:
    """Return the archive path for the EMPRESARIAL sheet."""
    wb_tree = ET.parse(zf.open("xl/workbook.xml"))
    rels_tree = ET.parse(zf.open("xl/_rels/workbook.xml.rels"))

    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    rid_to_target = {}
    for rel in rels_tree.findall(f"{{{rel_ns}}}Relationship"):
        rid_to_target[rel.attrib["Id"]] = rel.attrib["Target"]

    for sheet in wb_tree.findall(".//ns:sheet", NS):
        if sheet.attrib["name"].upper() == "EMPRESARIAL":
            rid = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            target = rid_to_target[rid]
            # Target is relative to xl/
            return f"xl/{target}"

    raise ValueError("Sheet 'EMPRESARIAL' not found in workbook")


def iter_sheet_rows(xlsx_path: str) -> list[dict[str, str]]:
    """Parse the EMPRESARIAL sheet and yield rows as {col_letter: value} dicts."""
    shared = parse_shared_strings(xlsx_path)
    rows = []

    with zipfile.ZipFile(xlsx_path) as zf:
        sheet_path = _find_empresarial_sheet(zf)
        tree = ET.parse(zf.open(sheet_path))

    for row_el in tree.findall(".//ns:row", NS):
        row_data: dict[str, str] = {}
        for cell in row_el.findall("ns:c", NS):
            ref = cell.attrib.get("r", "")
            m = _COL_RE.match(ref)
            if not m:
                continue
            col = m.group(1)

            cell_type = cell.attrib.get("t", "")
            v_el = cell.find("ns:v", NS)
            if v_el is None or v_el.text is None:
                continue

            if cell_type == "s":
                idx = int(v_el.text)
                value = shared[idx] if idx < len(shared) else ""
            else:
                value = v_el.text

            row_data[col] = value

        if row_data:
            rows.append(row_data)

    return rows


# ---------------------------------------------------------------------------
# Mapping & transformation
# ---------------------------------------------------------------------------

def map_row_to_lead(raw: dict[str, str]) -> dict:
    """Map a raw {col_letter: value} row to a normalized lead dict."""
    lead = {}
    for col, key in COLUMN_MAP.items():
        val = raw.get(col, "")
        lead[key] = val.strip() if isinstance(val, str) else val

    lead["has_email"] = bool(lead.get("email"))
    return lead


def deduplicate_leads(leads: list[dict]) -> list[dict]:
    """Remove duplicate leads by (company, email) — case-insensitive email."""
    seen: set[tuple[str, str]] = set()
    result = []
    for lead in leads:
        key = (lead.get("company", ""), lead.get("email", "").lower())
        if key not in seen:
            seen.add(key)
            result.append(lead)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def import_leads(xlsx_path: str) -> list[dict]:
    """Full pipeline: parse xlsx → map → score → dedupe.

    Returns a list of lead dicts with 'score' and 'recommended' fields added.
    """
    rows = iter_sheet_rows(xlsx_path)

    # Skip header row (first row where company == column header name)
    if rows and rows[0].get("A", "").strip() in ("Compañía", "Compania", "Company"):
        rows = rows[1:]

    leads = []
    for raw in rows:
        lead = map_row_to_lead(raw)
        # Skip completely empty rows
        if not lead.get("company") and not lead.get("email"):
            continue
        lead["score"] = score_lead(lead)
        lead["recommended"] = recommend(lead)
        leads.append(lead)

    return deduplicate_leads(leads)
