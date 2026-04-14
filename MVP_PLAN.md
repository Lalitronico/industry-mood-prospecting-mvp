# Industry Mood Prospecting MVP - Plan Redefinido

Fecha: 2026-04-13
Estado: Replanteado
Propósito: conseguir 2-3 demos mensuales para Industry Mood con un sistema semi-autónomo, human-in-the-loop y replicable después de la validación.

---

## 1. Tesis del MVP

El plan original intentaba construir una mini-plataforma de sales automation demasiado grande para el problema real.

Para Industry Mood, el MVP no debe optimizar elegancia arquitectónica; debe optimizar aprendizaje comercial:

1. Encontrar empresas reales del ICP local
2. Conseguir datos de contacto utilizables
3. Generar mensajes personalizados que Eduardo apruebe rápido
4. Enviar pocas piezas de outreach, pero de alta calidad
5. Aprender qué convierte a demo

La unidad de éxito no es “completar módulos”.
La unidad de éxito es: demos agendadas.

---

## 2. Objetivo operativo

Objetivo principal:
- Generar 2-3 demos mensuales para Industry Mood

Objetivos intermedios:
- Construir una base inicial de 50-100 leads reales del ICP
- Permitir revisar/aprobar 10-15 emails por día en menos de 20 minutos
- Ejecutar una secuencia simple de 3 pasos por email
- Documentar un workflow replicable para luego vender el sistema a otros clientes

---

## 3. ICP inicial

Segmento prioritario:
- Empresas manufactureras y retail
- 50-500 empleados
- Ciudad Juárez y Chihuahua

Señales de dolor prioritarias:
- Alta rotación
- Operaciones por turnos
- Plantillas grandes de personal operativo
- Vacantes frecuentes en RH, operaciones o supervisión
- Crecimiento, expansión o presión de contratación

Buyer personas iniciales:
- Dirección de RH
- Gerencia de RH
- Dirección de planta / operaciones
- Dirección general en empresas medianas

Hipótesis comercial:
Industry Mood tiene ventaja en este ICP porque combina:
- especialización en clima/rotación,
- velocidad de implementación,
- lenguaje más cercano al contexto regional,
- posibilidad de demo local o trato directo.

---

## 4. Qué conservar del plan anterior

Conservar:
- FastAPI como backend ligero
- SQLite para MVP
- Principio human-in-the-loop
- Email como canal inicial
- Concepto de lead/company/campaign como núcleo del sistema
- Visión de convertir esto después en producto replicable
- ICP local como wedge inicial

No conservar sin simplificar:
- modelos y tablas demasiado detallados
- analytics complejos
- dashboards pesados
- integraciones caras antes de validar el canal

---

## 5. Qué desechar

Desechar del MVP inicial:
- Apollo.io como fuente principal de leads
- dependencia en Clearbit, BuiltWith, StackShare y similares
- secuencia de 7 touchpoints
- dashboard Streamlit o React
- tracking avanzado de opens/clicks como prioridad
- ActivityLog como módulo central
- Kimi/Ollama local como requisito
- promesa de construir todo en 14 días
- metas genéricas tipo “100 leads/semana” sin validar TAM real

Racional:
El cuello de botella hoy no es software. Es calidad de lista, deliverability y mensaje.

---

## 6. Principios de diseño del nuevo MVP

1. Manual-first, automation-second
   - Primero validar el workflow manual asistido
   - Después automatizar lo repetitivo

2. Local-market realism
   - El ICP de Juárez/Chihuahua no se comporta como un SaaS B2B de EE.UU.
   - Muchas empresas requerirán investigación manual y contacto más artesanal

3. Human approval is core, not a temporary hack
   - La revisión humana protege marca, tono y deliverability

4. Few moving parts
   - Menos integraciones = menos fragilidad

5. Result-based phases
   - No avanzar por calendario sino por evidencia

---

## 7. Arquitectura mínima recomendada

### 7.1 Stack
- Backend/API: FastAPI
- Base de datos: SQLite
- ORM: SQLAlchemy
- Email sending: Resend o Gmail/Outlook manual al inicio
- AI writer: API de Claude o GPT
- Approval UI: HTML simple servido por FastAPI o CLI con rich
- Reportes: CSV + Google Sheets al principio

### 7.2 Modelo de datos mínimo

Reducir el sistema a 3 entidades centrales:

1. Lead
- company_name
- contact_name
- job_title
- email
- phone (opcional)
- city
- industry
- employee_range
- source
- pain_signal
- status
- priority
- notes
- last_contact_at
- next_contact_at

2. EmailDraft
- lead_id
- step_number
- subject
- body_text
- status: pending_review / approved / rejected / sent / replied / bounced
- generation_context
- reviewed_by
- reviewed_at
- scheduled_at
- sent_at

3. Campaign
- name
- segment
- active
- notes

Todo lo demás puede esperar.

---

## 8. Fuentes de leads realistas

Fuentes prioritarias para el ICP real:
- INDEX Juárez
- CANACINTRA
- CANACO
- directorios empresariales locales
- Google Maps + sitios corporativos
- OCC / Computrabajo / Indeed MX para detectar rotación o crecimiento
- LinkedIn manual
- recomendaciones y referrals

Principio operativo:
La primera base de leads se construye principalmente por investigación manual y luego se importa por CSV.

---

## 9. Canal inicial

Canal principal:
- Email

Canales complementarios a considerar después de validar:
- WhatsApp manual con templates sugeridos
- llamada telefónica
- contacto presencial / networking local

Regla:
No automatizar WhatsApp en el MVP.
Puede usarse como segundo canal manual cuando el email no responde.

---

## 10. Secuencia recomendada

En vez de 7 touchpoints, usar una secuencia de 3 pasos:

Paso 1. Email inicial
- muy personalizado
- 80-140 palabras
- CTA suave

Paso 2. Follow-up corto
- 3 a 5 días después
- recuerda el problema y reformula el valor

Paso 3. Último intento
- 5 a 7 días después
- cierra con elegancia y deja puerta abierta

Si no responde:
- mover a “recontactar en 60-90 días”
- o pasar a outreach manual complementario

---

## 11. Workflow objetivo

1. Eduardo identifica o importa leads vía CSV
2. El sistema normaliza y guarda la base
3. El sistema genera draft de email con IA
4. Eduardo revisa, corrige y aprueba
5. El sistema envía el email aprobado
6. Se registra estado básico de envío
7. Las respuestas se clasifican manualmente al inicio
8. Si no hay respuesta, el sistema propone siguiente draft

---

## 12. Fases redefinidas

### Fase 0 - Validación de lista
Objetivo:
probar que existe una base real de leads accesibles para este canal.

Entregables:
- plantilla CSV estándar
- script de importación CSV
- 50 leads reales del ICP en base de datos

Criterio de salida:
- al menos 50 leads importados
- al menos 30 con email utilizable

Si esta fase falla:
- no continuar construyendo automatización
- revisar ICP, canal o geografía

---

### Fase 1 - Generación y aprobación
Objetivo:
probar que el sistema reduce el tiempo de preparación de outreach.

Entregables:
- generador de email vía API de Claude/GPT
- 3 prompts base: inicial, follow-up, último intento
- interfaz mínima de revisión/aprobación

Criterio de salida:
- Eduardo puede revisar/aprobar 10-15 drafts en menos de 20 minutos

---

### Fase 2 - Envío básico
Objetivo:
probar que se puede operar el canal de forma consistente sin fricción operativa.

Entregables:
- integración mínima con Resend o flujo de envío manual asistido
- registro de sent_at y estado
- configuración de dominio/subdominio si aplica

Criterio de salida:
- 10-20 emails enviados correctamente
- sin errores operativos importantes

---

### Fase 3 - Secuencia de 3 pasos
Objetivo:
automatizar solo el siguiente mejor paso.

Entregables:
- scheduler simple o job manual diario
- reglas para follow-up 1 y último intento
- estados básicos de respuesta/no respuesta

Criterio de salida:
- primera cohorte completa recorriendo la secuencia de 3 pasos

---

### Fase 4 - Aprendizaje comercial
Objetivo:
mejorar conversión, no complejidad.

Entregables:
- análisis simple en CSV/Sheets
- clasificación de objeciones frecuentes
- variantes de messaging por subsector

Criterio de salida:
- 2-3 demos en un mes o evidencia clara de qué debe cambiarse

---

## 13. Roadmap funcional recomendado

Orden recomendado de construcción:

1. CSV import
2. modelo mínimo de lead/draft
3. generador de email
4. cola de aprobación
5. envío básico
6. follow-up simple
7. métricas mínimas

No construir todavía:
- frontend complejo
- scoring sofisticado
- tracking completo de engagement
- enriquecimiento automático multi-API
- CRM externo
- analytics avanzados

---

## 14. KPIs realistas

KPIs de validación temprana:
- leads reales identificados
- % de leads con email utilizable
- tiempo de revisión por batch
- emails enviados por semana
- reply rate
- positive reply rate
- demos agendadas

Benchmarks iniciales razonables para el MVP:
- 30-50 leads útiles en el primer ciclo
- 5-10 emails/día al inicio
- 1 demo en el primer mes como señal temprana positiva
- 2-3 demos/mes como objetivo de estabilización

Métrica reina:
- demos agendadas por mes

---

## 15. Riesgos críticos

1. No encontrar suficientes contactos válidos
Mitigación:
- validar la lista antes de seguir desarrollando

2. Deliverability pobre
Mitigación:
- warmup gradual
- SPF/DKIM/DMARC
- volumen bajo al inicio

3. Mensaje poco creíble o demasiado genérico
Mitigación:
- personalización basada en señales reales
- revisión humana estricta

4. Mercado local demasiado pequeño
Mitigación:
- medir TAM real y preparar expansión a otras ciudades/verticales

5. Overengineering
Mitigación:
- no abrir nuevas fases sin evidencia de la anterior

---

## 16. Recomendación técnica concreta para este repo

El repo actual debe reinterpretarse como base de workflow, no como producto casi terminado.

Cambios recomendados en la implementación:
- simplificar modelos actuales
- dejar fuera tablas y campos no esenciales
- construir primero importador CSV
- construir luego generador de drafts
- construir después una approval queue mínima
- postergar routers múltiples, analytics y features de CRM

En otras palabras:
este repo debe pasar de “SaaS outbound engine” a “lead research + draft generation + approval + send loop”.

---

## 17. Recomendación final

La mejor versión de este MVP no es una plataforma ambiciosa.
Es un sistema pequeño, feo, operable y medible.

Si el workflow manual-asistido logra demos:
- entonces tiene sentido productizar,
- automatizar más,
- y vender el sistema a terceros.

Si no logra demos:
- el aprendizaje será comercial, no técnico,
- y habrás evitado desperdiciar semanas construyendo software elegante para un canal no validado.

Resumen ejecutivo:
- Mantén backend simple
- valida lista primero
- usa IA solo para drafts
- conserva aprobación humana
- limita secuencia a 3 pasos
- mide demos, no features
