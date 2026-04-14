# Excel Profiling & First-Wave Segmentation Rules

Source file: `Empresarial AAA AA A y B.xlsx`

## Dataset overview

| Metric | Value |
|--------|-------|
| Total non-empty company rows | 15,615 |
| Rows for Chihuahua, Chih. | 112 |
| Rows for Juárez, Chih. | 77 |
| Total exact local rows (both geos) | 189 |
| Local rows with email | 189 (100%) |
| Local rows size A/AA/AAA | 172 (91%) |

## Local priority-role counts

| Role bucket | Count |
|-------------|-------|
| GM (Director/Gerente General, CEO) | 34 |
| HR (Recursos Humanos, Capital Humano) | 28 |
| OPS (Operaciones, Planta) | 16 |

## Top local company types

| Type | Count |
|------|-------|
| Empresa de servicio | 52 |
| Empresa comercial | 42 |
| Industria alimentaria | 18 |
| Cadena de tiendas | 10 |
| Industria automotriz | 7 |
| Industria del papel | 7 |
| Industria de materiales de construcción | 7 |
| Industria extractiva | 6 |
| Industria | 6 |
| Industria química | 5 |
| Industria metalmecánica | 4 |

## First-wave segmentation rules

A lead is recommended for initial Industry Mood outreach when **all** of the following hold:

1. **Has email** — mandatory (no email = score 0).
2. **Local geography** — city normalizes to `chihuahua` or `juarez` (+40 pts).
3. **Priority role** — GM or HR (+20 pts) or OPS (+15 pts). `OTHER` roles are explicitly excluded from first-wave recommendation.
4. **Target company type** — one of the 11 types listed above (+20 pts).
5. **Size A or above** — AAA (+20), AA (+15), A (+10), B (+5).

Score range: 0-100. Recommend threshold: **65**, plus the hard gate that the role must be GM/HR/OPS.

### Expected first-wave size

Using the current heuristic, the sheet yields roughly **81 recommended contact rows**, which collapse to about **45 unique companies** once multiple contacts per company are grouped. That is a good first outreach wave for a tightly controlled, human-reviewed MVP.

### Scoring module

See `scoring.py` — pure Python, no dependencies. Functions: `normalize_city`, `classify_role`, `is_target_type`, `score_lead`, `recommend`.
