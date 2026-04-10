# Industry Mood Prospecting MVP

Sistema semi-autónomo de prospección B2B para Industry Mood - diseñado para empresas manufactureras y retail en Ciudad Juárez y Chihuahua.

## 🎯 Objetivo

Automatizar la prospección de leads B2B con human-in-the-loop, generando 2-3 demos mensuales para Industry Mood.

## 📁 Estructura

```
industry-mood-prospecting-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Database models
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   └── templates/emails/    # Email templates
├── scripts/                 # Setup and utility scripts
├── tests/                   # Test suite
├── MVP_PLAN.md             # Plan completo
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python scripts/setup_db.py
```

### 3. Run Application

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access API

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 📊 Modelos de Datos

### Lead
- Contacto individual (email, nombre, cargo)
- Score de calificación (0-100)
- Estado en funnel
- Engagement tracking

### Company
- Información de empresa
- Señales de dolor (pain signals)
- Tecnologías utilizadas

### Campaign
- Campañas de outreach
- Secuencias de emails
- Métricas de performance

### Email
- Emails generados y enviados
- Workflow de aprobación
- Tracking (opens, clicks, replies)

## 🔧 Configuración

Variables de entorno (crear `.env`):

```env
DATABASE_URL=sqlite:///./industry_mood_prospecting.db
APOLLO_API_KEY=your_key_here
HUNTER_API_KEY=your_key_here
RESEND_API_KEY=your_key_here
```

## 📝 Plan de Implementación

Ver [MVP_PLAN.md](./MVP_PLAN.md) para detalles completos.

### Fases:
1. **Fase 0**: Setup (✅ Completado)
2. **Fase 1**: Core Backend (3 días)
3. **Fase 2**: Scraping & Enrichment (3 días)
4. **Fase 3**: AI Writer (2 días)
5. **Fase 4**: Approval UI (2 días)
6. **Fase 5**: Sender & Sequences (2 días)
7. **Fase 6**: Analytics (1 día)

## 💰 Costos Operativos

- Apollo.io: $49-99/mes
- Hunter.io: $49/mes
- Resend (email): $20/mes
- **Total**: ~$150/mes

## 📈 KPIs Objetivo

- Reply rate: >10%
- Positive reply: >3%
- Demo booking: >1%
- Throughput: 10-15 emails/día (revisados por humano)

## 👥 Target

**ICP**: Empresas medianas (50-500 empleados) en retail y manufactura en Ciudad Juárez y Chihuahua.

## 🛠️ Tecnologías

- **Backend**: FastAPI + SQLAlchemy
- **Database**: SQLite (MVP) → PostgreSQL (prod)
- **AI**: Kimi K2.5 (vía Ollama en ZBook)
- **Email**: Resend
- **Scraping**: Apollo.io API

## 📄 Licencia

Proyecto privado para Industry Mood.