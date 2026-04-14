# Industry Mood Prospecting MVP

Sistema semi-autónomo de prospección B2B para Industry Mood.

Objetivo inmediato:
validar un workflow pequeño y operable que ayude a generar 2-3 demos mensuales para el SaaS de pulse surveys de Industry Mood, con revisión humana en cada mensaje.

## Estado actual

Repositorio en reorientación hacia **Excel import + segmentation**.

Hoy contiene:
- esqueleto FastAPI (backend ligero)
- conexión SQLite con SQLAlchemy
- modelos iniciales
- script de setup de base de datos
- **scoring module** (`scoring.py`) — funciones puras para normalizar ciudad, clasificar rol, detectar tipo target, puntuar y recomendar leads
- **draft generator** (`drafts.py`) — templates role-aware (GM/HR/OPS) en español, personalización por empresa/ciudad/tipo/tamaño
- **approval queue** (`queue_db.py`) — SQLite con estados pending_review/approved/rejected
- **CLIs de drafts**: `generate_drafts.py`, `list_drafts.py`, `review_draft.py`
- **75 tests** en `tests/`
- **profiling y reglas de segmentación** en `docs/excel_profiling_and_segmentation.md`
- plan replanteado en `MVP_PLAN.md`

La fuente real de leads es un archivo Excel (`Empresarial AAA AA A y B.xlsx`) con 15,615 empresas; 189 locales exactas (Chihuahua + Juárez), todas con email.

No contiene todavía:
- envío real de campañas
- generación de drafts con IA (hoy usa templates; diseñado para swap fácil a LLM)

## Principio del MVP

Este proyecto ya no debe entenderse como una plataforma de sales automation completa.
Debe entenderse como un workflow asistido para:
1. importar leads reales,
2. generar drafts personalizados,
3. aprobarlos manualmente,
4. enviarlos,
5. aprender qué convierte a demo.

## Alcance inmediato

Fases prioritarias:
1. Validación de lista de leads
2. Generación y aprobación de drafts
3. Envío básico
4. Secuencia simple de 3 pasos
5. Iteración comercial

Detalles completos en `MVP_PLAN.md`.

## Estructura actual

```text
industry-mood-prospecting-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   └── models.py
├── docs/
│   └── excel_profiling_and_segmentation.md
├── scripts/
│   └── setup_db.py
├── tests/
│   ├── __init__.py
│   ├── test_scoring.py
│   ├── test_importer.py
│   ├── test_drafts.py
│   └── test_queue.py
├── scoring.py
├── importer.py
├── import_leads.py
├── drafts.py
├── queue_db.py
├── generate_drafts.py
├── list_drafts.py
├── review_draft.py
├── MVP_PLAN.md
├── README.md
└── requirements.txt
```

## Quick start

### 1. Crear entorno

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Inicializar base de datos

```bash
python scripts/setup_db.py
```

### 3. Correr API

```bash
uvicorn app.main:app --reload
```

### 4. Endpoints actuales

- `GET /`
- `GET /health`
- Docs: `http://localhost:8000/docs`

## Stack actual

- FastAPI
- SQLAlchemy
- SQLite
- Python

## Excel Importer

The importer reads the EMPRESARIAL sheet from the source `.xlsx` file using only Python stdlib (`zipfile` + `xml`). No openpyxl needed.

### Dry-run (summary only)

```bash
python import_leads.py "/mnt/c/Users/HP ZBOOK/Downloads/Empresarial AAA AA A y B.xlsx"
```

### Export recommended leads to CSV

```bash
python import_leads.py "/mnt/c/Users/HP ZBOOK/Downloads/Empresarial AAA AA A y B.xlsx" -o recommended.csv
```

### Export ALL leads (including non-recommended)

```bash
python import_leads.py "/mnt/c/Users/HP ZBOOK/Downloads/Empresarial AAA AA A y B.xlsx" --all -o all_leads.csv
```

### How it works

1. `importer.py` parses the `.xlsx` via `zipfile` + `xml.etree`
2. Maps columns (A=Compañía, B=Puesto, C=Nombre, D=Email, E=Tipo, F=Tamaño, J=Ciudad)
3. Normalizes and scores each lead via `scoring.py`
4. Deduplicates by (company, email)
5. Restricts first-wave recommendations to local GM/HR/OPS contacts
6. `import_leads.py` prints a summary and optionally writes a CSV

Current verified output on Eduardo's file:
- 15,617 deduplicated contact rows
- 81 recommended first-wave contacts
- 45 unique companies in the recommended set

### Running tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Draft Generation & Approval Queue

### 1. Generar drafts desde Excel a la cola de aprobación

```bash
python generate_drafts.py "/mnt/c/Users/HP ZBOOK/Downloads/Empresarial AAA AA A y B.xlsx"
```

Esto importa leads recomendados, genera un draft personalizado por cada uno (template role-aware en español), y los inserta en `drafts_queue.db` con status `pending_review`.

### 2. Ver drafts pendientes

```bash
python list_drafts.py                   # ver pendientes con cuerpo completo
python list_drafts.py --short           # resumen en una línea por draft
python list_drafts.py --all             # ver todos (incluyendo aprobados/rechazados)
python list_drafts.py --all --short     # resumen completo
```

### 3. Aprobar o rechazar drafts

```bash
python review_draft.py approve 1        # aprobar draft #1
python review_draft.py reject 2         # rechazar draft #2
python review_draft.py approve 1 2 3    # aprobar varios
```

### Arquitectura de drafts

- `drafts.py` — módulo de generación con templates por rol (GM/HR/OPS). Diseñado para que un LLM reemplace solo `generate_draft()` sin tocar el resto del pipeline.
- `queue_db.py` — cola SQLite con `init_queue`, `enqueue_draft`, `list_pending`, `get_draft`, `update_status`. Estados: `pending_review` → `approved` | `rejected`.

## Próxima implementación recomendada

Orden sugerido:
1. ~~importador Excel~~ ✓
2. ~~generación de drafts + cola de aprobación~~ ✓
3. swap de templates a generación con LLM (Claude/GPT)
4. envío básico con Resend o flujo manual asistido
5. secuencia simple de 3 pasos

> **Nota:** el repo ya no depende de scraping ni Apollo. La fuente primaria es el archivo Excel con datos empresariales reales.

## Nota estratégica

La métrica principal de este proyecto no es número de features construidas.
La métrica principal es demos agendadas.
