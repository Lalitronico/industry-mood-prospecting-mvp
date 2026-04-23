# Industry Mood Prospecting MVP

Sistema semi-autónomo de prospección B2B para generar demos de Industry Mood.

El repositorio implementa un workflow pequeño, barato y auditable para convertir una base Excel de empresas en drafts de outreach revisables, con cola de aprobación, suppression list, envío controlado y secuencia simple de 3 pasos.

La métrica principal no es número de features. La métrica principal es demos agendadas.

## Estado Actual

Estado: MVP operativo local, human-in-the-loop.

Ya funciona:

- Importar y puntuar leads desde `Empresarial AAA AA A y B.xlsx`.
- Filtrar una primera ola estricta del ICP local.
- Generar drafts personalizados por rol: GM, HR y OPS.
- Evitar duplicados al correr el generador varias veces.
- Revisar, aprobar, rechazar y listar drafts.
- Suprimir emails para no volver a contactarlos.
- Exportar drafts aprobados a CSV.
- Simular envío con `dry-run` o escribir mensajes a `outbox/`.
- Marcar drafts como enviados.
- Generar follow-ups vencidos para una secuencia de 3 pasos.
- Marcar respuestas y rebotes para detener la secuencia.
- Levantar un backend FastAPI mínimo con `/health`.
- Correr una suite de tests automatizados.

No funciona todavía:

- Envío real por Resend, SMTP, Gmail o Outlook.
- Generación de drafts con LLM.
- Tracking automático de replies desde inbox.
- UI web de aprobación.
- CRM completo o dashboard comercial.

## Datos Verificados

Fuente local esperada:

```bash
Empresarial AAA AA A y B.xlsx
```

El Excel real está incluido intencionalmente en este repositorio para que el workflow sea reproducible al compartirlo con el equipo.

Resultados verificados con el archivo actual:

- 15,617 contactos deduplicados.
- 189 contactos locales en Chihuahua/Juárez.
- 66 contactos recomendados para primera ola estricta.
- 37 empresas únicas en la primera ola.

Reglas de recomendación estricta:

- Tiene email.
- Ciudad normalizada a `chihuahua` o `juarez`.
- Rol prioritario: GM, HR u OPS.
- Tipo de empresa objetivo.
- Tamaño A, AA o AAA.
- Score mínimo de 65.

## Arquitectura

Módulos principales:

- `importer.py`: lee el Excel con `zipfile` y `xml`, sin depender de `openpyxl`.
- `scoring.py`: normaliza ciudad, clasifica rol, calcula score y recomienda leads.
- `drafts.py`: genera emails de step 1, step 2 y step 3 con templates por rol.
- `queue_db.py`: maneja la cola SQLite, estados, suppression list y reglas de follow-up.
- `sender.py`: abstrae el envío con backends `dry-run` y `file-outbox`.
- `app/main.py`: API FastAPI mínima.

CLIs disponibles:

- `import_leads.py`: importa, puntúa y exporta leads.
- `generate_drafts.py`: genera drafts iniciales.
- `list_drafts.py`: lista drafts pendientes o todos los estados.
- `review_draft.py`: aprueba o rechaza drafts.
- `suppress_email.py`: agrega/lista emails suprimidos.
- `send_drafts.py`: envía drafts aprobados usando backend controlado.
- `generate_followups.py`: genera follow-ups vencidos.
- `mark_outcome.py`: marca replies o bounces.
- `export_approved.py`: exporta drafts aprobados a CSV.

Estados de draft:

- `pending_review`: listo para revisión humana.
- `approved`: aprobado para envío.
- `rejected`: descartado.
- `suppressed`: bloqueado por suppression list, reply, bounce o decisión manual.
- `sent`: enviado o procesado por backend de salida.
- `replied`: el contacto respondió; se detiene la secuencia.
- `bounced`: el email rebotó; se suprime el contacto.

## Setup

Crear entorno:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Inicializar base de datos del backend:

```bash
python scripts\setup_db.py
```

Correr API:

```bash
uvicorn app.main:app --reload
```

Endpoints actuales:

- `GET /`
- `GET /health`
- Docs: `http://localhost:8000/docs`

## Workflow Operativo

### 1. Importar y revisar universo de leads

```bash
python import_leads.py "Empresarial AAA AA A y B.xlsx"
```

Exportar recomendados:

```bash
python import_leads.py "Empresarial AAA AA A y B.xlsx" -o recommended.csv
```

Exportar todos:

```bash
python import_leads.py "Empresarial AAA AA A y B.xlsx" --all -o all_leads.csv
```

### 2. Generar drafts iniciales

```bash
python generate_drafts.py "Empresarial AAA AA A y B.xlsx"
```

El comando es idempotente. Si ya existe un draft para el mismo email, campaña y paso, no lo duplica.

### 3. Revisar drafts

Ver pendientes completos:

```bash
python list_drafts.py
```

Ver resumen:

```bash
python list_drafts.py --short
```

Ver todos los estados:

```bash
python list_drafts.py --all --short
```

### 4. Aprobar o rechazar

```bash
python review_draft.py approve 1
python review_draft.py reject 2
python review_draft.py approve 1 2 3
```

### 5. Suprimir contactos

```bash
python suppress_email.py add contacto@empresa.com --reason unsubscribed
python suppress_email.py list
```

La suppression list evita nuevos drafts y bloquea el envío de drafts aprobados para ese email.

### 6. Enviar aprobados de forma controlada

Dry run:

```bash
python send_drafts.py --db drafts_queue.db --mode dry-run
```

File outbox:

```bash
python send_drafts.py --db drafts_queue.db --mode file-outbox --outbox outbox/
```

Los drafts enviados pasan a `sent` y no se reenvían.

### 7. Generar follow-ups

```bash
python generate_followups.py --db drafts_queue.db
```

Solo step 2:

```bash
python generate_followups.py --db drafts_queue.db --step 2
```

Solo step 3:

```bash
python generate_followups.py --db drafts_queue.db --step 3
```

Reglas actuales:

- Step 2 se genera 4 días después de enviar step 1.
- Step 3 se genera 7 días después de enviar step 2.
- Si el contacto está `replied`, `bounced` o `suppressed`, no se generan más follow-ups.
- Si ya existe el siguiente paso, no se duplica.

### 8. Marcar resultados

```bash
python mark_outcome.py replied 12 --db drafts_queue.db
python mark_outcome.py bounced 13 --db drafts_queue.db
```

`replied` detiene la secuencia y suprime drafts pendientes/aprobados del mismo contacto.

`bounced` detiene la secuencia y agrega el email a la suppression list.

### 9. Exportar aprobados

```bash
python export_approved.py --db drafts_queue.db -o approved.csv
python export_approved.py --db drafts_queue.db
```

## Seguridad de Datos

Archivos ignorados por Git:

- `*.xlsx`, excepto `Empresarial AAA AA A y B.xlsx`
- `*.xls`
- `*.csv`
- `*.db`
- `*.sqlite`
- `outbox/`
- `.env`

Esto evita subir bases SQLite locales, exports, outboxes y archivos adicionales de prospecting por accidente. La base `Empresarial AAA AA A y B.xlsx` es la única excepción versionada.

## Tests

```bash
python -m pytest -q
```

Estado actual:

```text
128 passed
```

## Roadmap

Completado:

- Importador Excel.
- Scoring estricto del ICP.
- Drafts iniciales con aprobación humana.
- Cola SQLite idempotente.
- Suppression list.
- Secuencia de 3 pasos.
- Estados de reply/bounce.
- Sender controlado sin envío real.
- Smoke test de FastAPI.

Siguiente recomendado:

1. Integrar envío real con Resend o SMTP.
2. Agregar configuración de dominio y deliverability: SPF, DKIM y DMARC.
3. Agregar LLM para drafts con contexto real de cada empresa.
4. Crear una UI mínima de revisión/aprobación.
5. Registrar métricas comerciales: sent, replied, positive reply, demo booked.

## Nota Estratégica

Este repo no debe convertirse todavía en una plataforma grande de sales automation.

La versión correcta del MVP es un sistema pequeño, medible y supervisado que ayude a validar si el canal puede generar demos para Industry Mood sin poner en riesgo reputación, deliverability ni cumplimiento.
