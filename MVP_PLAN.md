# Industry Mood Prospecting MVP - Plan de Implementación

**Fecha**: 2026-04-10
**Estado**: Planificación - Pendiente respuestas a 6 preguntas clave
**Propósito**: Sistema semi-autónomo de prospección B2B para Industry Mood (test case → replicable)

---

## 1. Resumen Ejecutivo

### Qué es Industry Mood
- **Producto**: SaaS de employee pulse surveys + detección de riesgos (burnout, turnover)
- **Análisis**: 8 dimensiones del clima laboral
- **Pricing**: Desde $79/mes
- **URL**: https://www.industrymood.com/
- **Target ideal**: Empresas 50-500 empleados con problemas de retención

### Objetivo del MVP
Crear un sistema que:
1. Identifique leads calificados automáticamente
2. Genere outreach personalizado (human-in-the-loop)
3. Gestione el funnel hasta demo booking
4. Sea replicable para otros productos B2B

---

## 2. Arquitectura Técnica

### Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLite (MVP) → PostgreSQL (producción)
- **Task Queue**: Celery + Redis (opcional para V2)
- **Frontend**: Streamlit o React (solo dashboard admin)
- **Integraciones**: Apollo.io, Hunter.io, SendGrid/Resend, Calendly

### Estructura de Directorios
```
industry-mood-prospecting-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB connection
│   ├── routers/
│   │   ├── leads.py         # CRUD leads
│   │   ├── campaigns.py     # Gestión campañas
│   │   └── sequences.py     # Email sequences
│   ├── services/
│   │   ├── scraper.py       # Búsqueda de leads
│   │   ├── enrichment.py    # Enriquecimiento datos
│   │   ├── ai_writer.py     # Generación emails
│   │   ├── sender.py        # Envío emails
│   │   └── analytics.py     # Métricas
│   └── templates/
│       └── emails/          # Templates Jinja2
├── scripts/
│   ├── setup_db.py
│   └── seed_data.py
├── tests/
├── config.yaml
├── requirements.txt
└── README.md
```

---

## 3. Módulos del Sistema

### Módulo 1: Lead Discovery (Scraper)
**Función**: Encontrar empresas que encajen en el ICP

**Fuentes**:
- Apollo.io API (principal)
- LinkedIn Sales Navigator (export manual)
- Clutch.co / G2 (para agencias)
- Directorios sectoriales

**Filtros aplicables**:
- Tamaño: 50-500 empleados
- Industria: Tech, consultoría, servicios profesionales
- Ubicación: LATAM (inicial) → US/UE (expansión)
- Señales: Hiring en HR/People ops, crecimiento reciente

**Output**: Lista de empresas con datos básicos

---

### Módulo 2: Lead Enrichment
**Función**: Completar datos de contacto y empresa

**Datos a obtener**:
- Email de decisor (C-level, VP People, HR Director)
- Teléfono (opcional)
- LinkedIn profile
- Tecnologías usadas (StackShare, BuiltWith)
- Noticias recientes (funding, expansión, layoffs)
- Empleados totales, fecha de fundación

**Proveedores**:
- Hunter.io / ZeroBounce (emails)
- Clearbit / Apollo (enriquecimiento)
- Scraping de LinkedIn (con cuidado)

**Output**: Lead completo con score inicial

---

### Módulo 3: Scoring & Prioritization
**Función**: Calificar leads antes de contactar

**Criterios de scoring (0-100)**:
- Fit con ICP: +30 puntos
- Señal de dolor (hiring HR, comentarios Glassdoor negativos): +25 puntos
- Tamaño óptimo (100-300 emp): +20 puntos
- Presupuesto indicado (funding reciente): +15 puntos
- Contacto directo disponible: +10 puntos

**Buckets**:
- 80-100: Hot (contactar inmediatamente)
- 60-79: Warm (contactar esta semana)
- 40-59: Cool (nurture sequence)
- <40: Discard

---

### Módulo 4: AI Outreach Writer
**Función**: Generar emails personalizados

**Inputs para personalización**:
- Datos de la empresa (industria, tamaño, ubicación)
- Noticias/recientes eventos
- Pain points inferidos
- Rol del destinatario

**Estructura del email**:
1. Hook personalizado (1 línea sobre su empresa)
2. Value prop específica para su industria/tamaño
3. Social proof (si existe del sector)
4. Soft CTA (no "book a demo", sí "¿vale la pena explorar?")
5. Unsubscribe link (GDPR compliant)

**Human-in-the-loop**:
- Todos los emails generados van a cola de "Pendiente de aprobación"
- UI para revisar, editar, aprobar/rechazar
- Solo se envían los aprobados

**Modelo**: Kimi K2.5 (vía Ollama en ZBook) o GPT-4 (si hay budget)

---

### Módulo 5: Campaign Manager
**Función**: Gestionar secuencias de contacto

**Sequence típica (7 touchpoints)**:
1. Día 0: Email inicial personalizado
2. Día 3: Follow-up corto (¿viste el anterior?)
3. Día 7: LinkedIn connection request
4. Día 10: Email con case study del sector
5. Día 14: Break-up email
6. Día 21: Re-engagement (nuevo ángulo)
7. Día 45: Loop a nurture (newsletter mensual)

**Reglas**:
- Si responde positivo → Mover a "Interested", notificar vendedor
- Si responde negativo → Mover a "Rejected", log razón
- Si no responde → Continuar sequence
- Si bounce → Marcar email inválido, buscar alternativo

---

### Módulo 6: Analytics & Dashboard
**Función**: Medir y optimizar

**Métricas principales**:
- Leads generados por semana
- Email delivery rate
- Open rate
- Reply rate (target: >10%)
- Positive reply rate (target: >3%)
- Demo booked rate (target: >1%)
- Costo por lead cualificado

**Dashboards**:
1. Overview: Funnel completo, números clave
2. Campaign Performance: Comparativa por campaña
3. Lead Quality: Scores, fuentes más productivas
4. Email Performance: Templates que funcionan

---

## 4. Flujo de Trabajo (8 pasos)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DEFINE ICP                                               │
│    → Tamaño, industria, ubicación, pain points              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONFIGURA FUENTES                                        │
│    → Apollo.io, filtros de búsqueda, palabras clave         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. SCRAPEA LEADS                                            │
│    → Ejecuta scraper, obtiene lista base de empresas        │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. ENRIQUECE DATOS                                          │
│    → Emails, contactos, tecnologías, noticias               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. SCOREA Y PRIORIZA                                        │
│    → Algoritmo de scoring, bucket en Hot/Warm/Cool          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. GENERA OUTREACH                                          │
│    → AI escribe emails personalizados                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. REVISA Y APRUEBA                                         │
│    → Human-in-the-loop: revisar, editar, aprobar            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. ENVÍA Y NURTURE                                          │
│    → Schedule send, track replies, secuencia automática     │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Preguntas Pendientes (Bloqueantes)

Antes de empezar a construir, necesitamos claridad en:

### ✅ Pregunta 1: Definición del ICP - RESPONDIDA

**Perfil objetivo**:
- **Industrias**: Retail, manufactura, empresas de servicios
- **Tamaño**: Medianas empresas (50-500 empleados)
- **Ubicación**: Ciudad Juárez y Chihuahua (inicial)
- **Señales de dolor**: Alta rotación, operaciones 24/7, seasonal workers, múltiples turnos

**Justificación**: Mercado local donde Industry Mood tiene ventaja competitiva (conocimiento del contexto laboral regional, cercanía para demos presenciales).

---

### ✅ Pregunta 2: Oferta a Pitch - RESPONDIDA

**Plan recomendado (decisión Kimaru)**:
- **Plan**: "Growth" de $79/mes (entry point accesible)
- **Trial**: 14 días gratuito (sin tarjeta de crédito)
- **Diferenciador**: "Pulse surveys diseñados para empresas manufactureras y retail de Chihuahua" (localización + especialización)
- **Onboarding**: Setup completo incluido, primer survey en 48 horas
- **Garantía**: Si no ves mejoras en retención en 90 días, te devolvemos el dinero

**Value prop para email**: *"Reducir la rotación en tu industria es difícil cuando no sabes qué piensan tus equipos. Industry Mood te da insights en tiempo real para retener talento clave."*

---

### ✅ Pregunta 3: Canal de Outreach - RESPONDIDA

**Canal**: Email únicamente (para empezar)

**Stack recomendado**:
- **Email verification**: Hunter.io (starter plan $49/mes)
- **ESP**: Resend (emails desde dominio propio, mejor deliverability que SendGrid para B2B en MX)
- **Dominio**: Recomendable usar subdominio (ej: outreach.industrymood.com) para proteger reputación del dominio principal

---

### ✅ Pregunta 4: Workflow de Aprobación - RESPONDIDA

**Revisor**: Eduardo (Lalo) revisa todos los emails

**Throughput recomendado (decisión Kimaru)**:
- **Batch**: 10-15 emails por día (lunes a viernes)
- **Tiempo estimado**: 15-20 minutos diarios
- **Formato**: Vista tipo "inbox" con preview, aprobar/rechazar/editar rápido
- **Deadline**: Emails generados hoy se envían mañana (si se aprueban antes de las 6 PM)

**Rationale**: 10-15 emails/day = ~250-300 emails/mes = suficiente para generar 2-3 demos/mes con tasas conservadoras.

---

### ✅ Pregunta 5: Base de Datos Existente - RESPONDIDA

**Estado**: Sin leads confirmados, crear base desde cero

**Estrategia**:
- **Semana 1**: Scrapeo inicial de 50 empresas target (Juárez + Chihuahua)
- **Industrias**: Retail grande (supermercados, tiendas departamentales), maquiladoras, empresas de logística
- **Fuentes**: Directorio de CANACINTRA, CANACO, LinkedIn, sitios de empleo (donde publican)
- **Contactos**: Buscar CEOs, Directores de RH, Gerentes de Planta
- **Meta**: Tener 100 leads calificados en la base antes de enviar primer email

---

### ✅ Pregunta 6: Integración CRM - RESPONDIDA

**Estado actual**: Sin CRM

**Estrategia**:
- **MVP**: No integrar CRM externo, usar el propio del sistema (tablas en SQLite)
- **Export**: Función "Export to CSV" para migrar a CRM cuando se implemente
- **Fase 2 (post-MVP)**: Evaluar HubSpot (gratuito hasta 1,000 contactos) o Pipedrive
- **Pipeline stages**: Lead → Contacted → Interested → Demo Scheduled → Proposal Sent → Closed Won/Lost

---

## 6. Roadmap de Implementación

### Fase 0: Setup (1 día)
- [ ] Crear estructura de directorios
- [ ] Setup FastAPI + SQLite
- [ ] Configurar entorno virtual
- [ ] Crear modelos de datos base

### Fase 1: Core Backend (3 días)
- [ ] Implementar Lead model + CRUD API
- [ ] Implementar Campaign model
- [ ] Implementar Email Template system
- [ ] Crear endpoints básicos

### Fase 2: Scraping & Enrichment (3 días)
- [ ] Integrar Apollo.io API
- [ ] Implementar búsqueda con filtros
- [ ] Implementar enriquecimiento básico
- [ ] Crear script de importación masiva

### Fase 3: AI Writer (2 días)
- [ ] Diseñar prompts para email generation
- [ ] Integrar con modelo (Ollama → Kimi K2.5)
- [ ] Crear sistema de templates Jinja2
- [ ] Implementar personalización por industria

### Fase 4: Approval UI (2 días)
- [ ] Crear dashboard Streamlit
- [ ] Vista de cola de aprobación
- [ ] Editor de emails inline
- [ ] Botones Aprobar/Rechazar/Editar

### Fase 5: Sender & Sequences (2 días)
- [ ] Integrar SendGrid/Resend
- [ ] Implementar scheduler de envíos
- [ ] Crear lógica de sequences
- [ ] Tracking de opens/clicks/replies

### Fase 6: Analytics (1 día)
- [ ] Métricas básicas
- [ ] Dashboard de funnel
- [ ] Export de reports

**Total estimado**: 14 días de trabajo (con preguntas respondidas)

---

## 7. Costos Operativos Estimados (Mensual)

| Servicio | Costo | Uso |
|----------|-------|-----|
| Apollo.io API | $49-99/mes | Lead discovery |
| Hunter.io | $49/mes | Email verification |
| SendGrid/Resend | $20/mes | Email sending (hasta 50k) |
| OpenAI API (alternativa) | $30/mes | Si no usamos Ollama |
| VPS (actual) | $0 | Ya pagado |
| **Total** | **~$150/mes** | |

---

## 8. Success Metrics (KPIs)

### Métricas del Sistema
- **Leads/week**: 100 nuevos leads generados
- **Email delivery**: >95%
- **Open rate**: >25%
- **Reply rate**: >10%
- **Positive reply**: >3%
- **Demo booked**: >1%

### Métricas de Negocio
- **CAC** (Customer Acquisition Cost) objetivo: <$500
- **LTV/CAC ratio**: >3x
- **Time to first demo**: <7 días desde primer contacto

---

## 9. Próximos Pasos

1. **Responder las 6 preguntas bloqueantes** (necesito tu input)
2. **Decidir fecha de inicio** de Fase 0
3. **Confirmar presupuesto** para herramientas (~$150/mes)
4. **Asignar quién revisa emails** (human-in-the-loop)

---

## Notas

- Este MVP es **test case** para Industry Mood, pero diseñado para ser **replicable** a otros productos B2B
- La clave del éxito: **human-in-the-loop** en el outbound, no automatizar 100%
- Escalabilidad: Si funciona, el mismo sistema puede prospectar para Arquetype, Project Ollin, etc.

---

*Documento creado por Kimaru para Eduardo Vera | 2026-04-10*
