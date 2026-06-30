# ARQUITECTURA COMPLETA — Hint Media LinkedIn Outreach System
> Auditoría CTO · 30/06/2026 · Estado real del sistema, sin suposiciones.

---

## 1. VISIÓN GENERAL DEL SISTEMA

Este sistema comenzó como un generador de mensajes LinkedIn. Hoy es un **sistema híbrido de inteligencia comercial B2B** con pipeline de datos, enriquecimiento con IA, analítica y automatización parcial del envío.

### Flujo completo end-to-end

```
USUARIO (Florencia, CMO Hint Media)
│
│  opción 1: extensión Chrome
├─► EXTENSIÓN CHROME (extension/)
│     content.js: scraping automático del perfil LinkedIn
│     popup.js: UI inline con SYSTEM propio
│     background.js: envío automático de burbujas con delays random
│     └─► POST http://localhost:3000/api/generate ──┐
│                                                    │
│  opción 2: web app                                 │
└─► WEB APP (index.html en browser)                  │
      usuario pega texto del perfil                  │
      selecciona idioma + tono                       │
      click "Generar"                                │
      └─► POST http://localhost:3000/api/generate ──┘
                                                     │
                                                     ▼
                                          SERVIDOR (servidor.py)
                                          puerto 3000
                                          ├─ GET  / → sirve index.html
                                          ├─ POST /api/generate → llama Anthropic API
                                          ├─ GET  /api/historial → lee historial.json
                                          ├─ POST /api/historial → escribe historial.json (upsert)
                                          └─ POST /api/sync → git add/commit/push historial.json
                                                     │
                                                     ▼
                                          ANTHROPIC API
                                          modelo: claude-haiku-4-5-20251001
                                          prompt caching activado (ephemeral)
                                          max_tokens: 4000
                                                     │
                                          ┌──────────┴──────────┐
                                          │   GENERACIÓN        │
                                          │   INICIAL           │
                                          │   (generateOpeners) │
                                          └──────────┬──────────┘
                                                     │
                                          respuesta: 4+ secciones
                                          - Análisis estratégico
                                          - VARIANTE A (MSG1 + MSG2)
                                          - VARIANTE C (MSG1 + MSG2)
                                          - MSG3 / MSG4 / SEG1 / SEG2 (placeholders)
                                          - Scores, clasificación, confianza
                                                     │
                                                     ▼
                                          USUARIO elige variante
                                          (click "Usar esta")
                                                     │
                    ┌────────────────────────────────┤
                    │  WEB APP                       │  EXTENSIÓN
                    │  copia manual                  │  envío automático
                    │  pega en LinkedIn              │  de burbujas
                    └────────────────────────────────┘
                                                     │
                                          LINKEDIN (manual o extensión)
                                          MSG1 enviado: 3 burbujas
                                                     │
                                          el prospecto responde (o no)
                                                     │
                                                     ▼
                                          USUARIO pega la respuesta en
                                          el hilo de conversación (conv-thread)
                                          click "Sugerir respuesta" (handleReply)
                                                     │
                                                     ▼
                                          ANTHROPIC API
                                          contexto: historial conversación completo
                                          detecta: ENGAGEMENT_LEVEL (HIGH/MED/LOW)
                                          genera: MSG2 o respuesta contextual
                                                     │
                                          ┌──────────┴──────────┐
                                          si ENGAGEMENT permite  │
                                          → MSG2 con CTA dossier │
                                          └──────────────────────┘
                                                     │
                                          DOSSIER ENVIADO (fuera del sistema)
                                          manualmente por Florencia
                                                     │
                                                     ▼
                                          SEG1 generado por handleReply
                                          (clasifica engagement, elige modo)
                                                     │
                                                     ▼
                                          DATOS PERSISTIDOS
                                          ├─ historial.json (427 entradas)
                                          │   escritas por: extensión (automático)
                                          │               web app (manual, via histUpsert)
                                          └─ conversaciones/*.md (140+ archivos)
                                              escritos manualmente por Claude Code
                                              en sesiones de trabajo
                                                     │
                                          ┌──────────┴──────────────────────┐
                                          │  PIPELINES OFFLINE              │
                                          │                                 │
                                          ▼                                 ▼
                               dataset_builder/               ai_enrichment/
                               lee conversaciones/*.md        lee dataset.json
                               + historial.json               + needs_ai_review.csv
                               regex + heurísticas            llama Claude haiku
                               sin IA                         completa campos vacíos
                               output: dataset.json           output: enriched_dataset.csv
                               + stats.json                   + suggested_values.csv
                               + report.md                    + enrichment_report.md
                               + needs_ai_review.csv
                                          │
                                          ▼
                               historial_report.py
                               lee historial.json
                               calcula embudo completo
                               output: historial_dataset.json
                                       historial_report.md
                                          │
                                          ▼
                               ANALYTICS (analytics.html)
                               dashboard visual para el jefe
                               lee historial_dataset.json
                               (o data hardcodeada en el HTML)
                               KPIs + embudo + sectores + costos

                               VIEWER (viewer.html / historial.pages.dev)
                               versión pública del historial
                               lee historial.json desde Cloudflare Pages
```

---

## 2. MAPA COMPLETO DE CARPETAS

### `/` (raíz del proyecto)
**Objetivo:** Aplicación principal de generación de mensajes.

| Archivo | Función |
|---|---|
| `index.html` | UI web completa (2235 líneas). CSS + JS + SYSTEM prompt + toda la lógica del cliente. Monolito. |
| `servidor.py` | HTTP server Python. 4 endpoints. Proxy hacia Anthropic API. Escribe historial.json con lock threading. |
| `historial.json` | Base de datos única del programa. 427 entradas. Fuente de verdad operacional. |
| `analytics.html` | Dashboard HTML estático (661 líneas) para el jefe. KPIs, embudo, sectores, costos API. |
| `viewer.html` | Viewer público del historial (691 líneas). Se despliega en Cloudflare Pages. |
| `analytics.pdf` | PDF generado del analytics.html para presentaciones. |
| `requirements.txt` | Solo una dependencia: `httpx`. |
| `Procfile` | Para deploy en plataformas tipo Heroku (no se usa actualmente). |
| `.env.local` | API key de Anthropic. NO committeado. Leído por servidor.py al arrancar. |
| `CLAUDE.md` | Reglas críticas del proyecto para Claude Code. Tiene prioridad sobre memoria. |
| `hint_media.md` | Documento de contexto de la agencia. No lo consume ningún script automáticamente. |
| `contexto_para_chatgpt.txt` | Texto de contexto generado manualmente para consultas a ChatGPT. |
| `feedback_fixes.md` | Log de fixes y aprendizajes de sesiones. No lo consume ningún script. |
| `AUDITORIA_SISTEMA.md` | Auditoría anterior (parcial). No se usa como input en ningún pipeline. |

**Dependencias:** servidor.py necesita `.env.local`. index.html necesita `servidor.py` corriendo en :3000.

---

### `/extension/`
**Objetivo:** Chrome Extension que automatiza el scraping de perfiles y el envío de mensajes directamente en LinkedIn.

| Archivo | Función |
|---|---|
| `manifest.json` | MV3. Permisos: `activeTab`, `scripting`, `storage`, `tabs`. Host: `linkedin.com` + `localhost:3000`. |
| `popup.js` | UI del popup (742 líneas). SYSTEM prompt propio (duplicado del index.html, pero versión anterior con 2 variantes en vez de 4). Scraping, generación, envío. Estado en `chrome.storage.local`. |
| `popup.html` | Estructura HTML del popup. |
| `content.js` | Se inyecta en LinkedIn. Scraping del DOM del perfil. Apertura de chat. Envío de burbujas (fallback). |
| `background.js` | Service Worker. Orquesta el envío real de burbujas. Delays random 4-6s entre burbujas. POST a `/api/historial` tras envío. |

**Dependencias:** Necesita `servidor.py` corriendo en localhost:3000 para llamar a la API.

**INCERTIDUMBRE:** No está claro si la extensión está instalada y en uso activo hoy, o si solo se usa la web app.

---

### `/conversaciones/`
**Objetivo:** Archivo histórico de todas las conversaciones individuales. Son archivos `.md` escritos manualmente.

- **140+ archivos** `.md`, uno por prospecto.
- **Formato:** Markdown con campos en negrita (`**Campo:** valor`) y secciones `## MSG1`, `## Respuesta`, `## MSG2`, `## Dossier`, `## SEG1`, `## SEG2`, `## Notas`.
- **Quién los escribe:** Claude Code durante sesiones de trabajo, copiando la conversación real de LinkedIn.
- **Quién los lee:** `dataset_builder/dataset_builder.py` (regex, sin IA).
- **Problema conocido:** La cobertura de campos estructurados depende de cuán consistente fue la redacción del `.md`. Antes del 18/06/26 no se guardaba `profileRaw`.

---

### `/dataset_builder/`
**Objetivo:** Pipeline regex/heurísticas que transforma `conversaciones/*.md` en dataset estructurado. Sin IA.

| Archivo | Función |
|---|---|
| `config.py` | Constantes y reglas: SECTOR_RULES (regex por empresa/cargo), SENIORITY_RULES, OBJECTION_RULES, ENGAGEMENT_EXPLICIT_RE, CALL_KEYWORDS, etc. |
| `extractors.py` | Parser de archivos `.md`. Detecta 2 formatos: markdown plano y frontmatter YAML. Extrae campos bold, secciones `##`, bloques `>`. |
| `heuristics.py` | Aplica reglas de clasificación sobre el dict crudo. detect_sector, detect_seniority, detect_variante, detect_engagement, detect_objecion, etc. |
| `analytics.py` | Calcula stats.json y genera report.md a partir del dataset ya construido. |
| `dataset_builder.py` | Orquestador principal. Lee `.md`, llama extractors → heuristics → analytics. Escribe 5 outputs. |
| `historial_report.py` | Script separado que lee `historial.json` (no las `.md`) y genera reporte del embudo completo. |

**Outputs producidos:**
- `outputs/dataset.csv` / `dataset.json` — dataset estructurado de conversaciones/.md
- `outputs/needs_ai_review.csv` — filas con campos críticos vacíos (candidatos a enriquecimiento IA)
- `outputs/stats.json` / `report.md` — métricas del dataset
- `outputs/historial_dataset.json` — dataset del embudo (de historial.json)
- `outputs/historial_report.md` — reporte legible del embudo

**Ejecución:** Manual. `python dataset_builder/dataset_builder.py` y `python dataset_builder/historial_report.py`.

---

### `/ai_enrichment/`
**Objetivo:** Pipeline IA que completa campos vacíos del dataset usando Claude haiku. Paso posterior y opcional al dataset_builder.

| Archivo | Función |
|---|---|
| `config.py` | Rutas, modelo (haiku), TARGET_FIELDS, VALID_VALUES (enums por campo), CONFIDENCE_LEVELS. |
| `enrichment_pipeline.py` | Orquestador. Lee needs_ai_review.csv, llama Claude por fila, valida confidence, separa HIGH/MEDIUM (aplicados) de LOW (sugeridos). |
| `enrichment_prompts.py` | SYSTEM + builder del prompt por campo. |
| `enrichment_validator.py` | Guardrails: valida que el valor esté en el enum permitido, que la evidencia no esté vacía, que confidence sea HIGH/MEDIUM/LOW. |
| `confidence_engine.py` | Motor de confianza. Clasifica qué tan fiable es la inferencia IA. |
| `semantic_enrichment.py` | Variante semántica del enrichment (experimental, no es el pipeline principal). |
| `dossier_verification.py` | Script para verificar si el dossier fue enviado según el `.md`. |
| `build_audit_sample.py` | Genera muestra para auditoría manual. |
| `compute_precision.py` | Calcula precisión real del enrichment comparando con revisión manual. |
| `conversion_report.py` | Reporte de conversión del enrichment. |

**Outputs:**
- `outputs/enriched_dataset.csv` — campos completados con HIGH/MEDIUM confidence
- `outputs/suggested_values.csv` — campos LOW confidence, NO aplicados al dataset
- `outputs/enrichment_report.md` / `enrichment_stats.json`
- `outputs/audit_report.md` / `precision_result.json` / `semantic_audit_sample.csv`

**INCERTIDUMBRE:** No está claro si el enrichment se integra de vuelta al dataset principal o si queda como capa separada sin uso downstream.

---

### `/presentaciones/`
**Objetivo:** Material para reuniones comerciales. Generado ad-hoc por Claude Code.

Contiene PDFs, PPTXs y HTMLs del caso Luis Pérez/Foamtec (primera reunión del programa), CGC propuesta, y guiones de pitch. **No hay scripts que los consuman automáticamente.**

---

## 3. MAPA DE ARCHIVOS CLAVE

### `index.html` (2235 líneas)
- **Qué hace:** UI completa de la web app. Generación de MSG1/MSG2/SEG1. Hilo de conversación. Historial. Panel "Próximos" (pipeline de seguimiento).
- **Quién lo usa:** Florencia Di Rado (CMO) directamente en browser.
- **Cuándo corre:** Siempre que servidor.py está corriendo.
- **Consume:** Texto de perfil (input manual) → llama `POST /api/generate`.
- **Produce:** Mensajes para copiar/pegar. Guarda entrada en historial vía `POST /api/historial`.
- **Problema crítico:** El archivo tiene **2 instancias del SYSTEM prompt** (una en `const SYSTEM` y otra duplicada dentro del prompt de `generateOpeners()`). Esto es deuda técnica conocida.
- **JS en el archivo:** ~1600 líneas. Todo inline. Sin imports. Sin bundler.

### `servidor.py` (162 líneas)
- **Qué hace:** HTTP server minimalista. 4 endpoints. Proxy puro hacia Anthropic. Persistencia en `historial.json` con threading lock.
- **Quién lo usa:** index.html (web app) + extensión Chrome + historial_report.py (indirectamente, lee el mismo archivo).
- **Cuándo corre:** Manual. `python servidor.py`.
- **Consume:** `.env.local` (API key), peticiones HTTP.
- **Produce:** Respuestas de la API, modificaciones a `historial.json`.
- **Riesgo:** No hay autenticación. CORS abierto (`*`). Funciona solo en localhost, lo cual lo hace razonablemente seguro.

### `historial.json` (427 entradas)
- **Qué hace:** Base de datos operacional del programa.
- **Quién escribe:** `background.js` (extensión) vía POST `/api/historial` tras envío automático. También `index.html` vía `histUpsert` cuando el usuario elige variante en la web app.
- **Quién lee:** `index.html` (historial UI), `historial_report.py`, `dataset_builder.py` (fallback de campos).
- **Estructura de cada entrada:**
  ```json
  {
    "id": 1718051234567,        // timestamp Unix ms
    "date": "DD/MM/YY",
    "name": "Nombre Prospecto",
    "empresa": "Empresa SA",
    "variantTitle": "Variante A",
    "profileRaw": "texto del perfil LinkedIn...",  // desde 18/06/26
    "msg1": "burbuja1\n\nburbuja2\n\nburbuja3",
    "msg2": "burbuja1\n\nburbuja2...",
    "extraMsgs": { "MSG3": [], "MSG4": [], "SEG1": [], "SEG2": [] },
    "conversationHistory": [{ "role": "received|sent", "text": "..." }],
    "stage": 1,                 // 1-5
    "stageHistory": [{ "stage": 1, "date": "...", "note": "" }],
    "dossierMail": false
  }
  ```
- **Stage labels:** 1=MSG1 generado, 2=MSG2/contacto, 3=Dossier enviado, 4=Seguimiento, 5=Avanzado/reunión.
- **IMPORTANTE:** `stage` lo actualiza la web app manualmente. `extraMsgs.SEG1` es generado especulativamente con el perfil inicial, NO refleja el SEG1 real que se envió (que se genera en `handleReply` con contexto de conversación real).

### `extension/popup.js` (742 líneas)
- **Qué hace:** App completa de la extensión. Scraping → generación → selección → envío.
- **SISTEMA PROPIO DUPLICADO:** Tiene su propio `const SYSTEM` diferente al de `index.html`. La extensión genera **2 variantes** (A y C). La web app genera **4 variantes** con más capas de análisis.
- **Estado:** `chrome.storage.local` (persiste entre cierres del popup).

---

## 4. FLUJO DE DATOS

```
FUENTES DE ENTRADA:
│
├─ Texto del perfil LinkedIn (input manual o scraping automático)
├─ Respuestas del prospecto (input manual copiado de LinkedIn)
└─ historial.json (persiste entre sesiones)

FLUJO PRINCIPAL (operacional, diario):

Perfil LinkedIn (texto)
        │
        ▼
generateOpeners() en index.html
        │ POST /api/generate
        ▼
servidor.py → Anthropic API (haiku, prompt caching)
        │
        ▼
Respuesta parseada: análisis + variantes A/C + extraMsgs
        │
        ▼
Usuario elige variante → histUpsert() → POST /api/historial
        │
        ▼
historial.json (upsert por id, threading lock)
        │
        ▼ (tras respuesta del prospecto)
handleReply() → POST /api/generate
  (conversationHistory completo como contexto)
        │
        ▼
ENGAGEMENT_LEVEL detectado
MSG2 o respuesta contextual generada
        │
        ▼ (si acepta dossier)
stage actualizado a 3 → POST /api/historial
        │
        ▼ (tras dossier)
handleReply() → SEG1 generado según ENGAGEMENT_LEVEL
stage → 4

FLUJO PARALELO (archivo manual, para análisis):

Conversación real de LinkedIn
        │
        ▼
Claude Code escribe conversaciones/[nombre].md
        │
        ▼
dataset_builder.py (manual, sin IA)
  extractors.py → parse .md
  heuristics.py → clasificación por regex
  analytics.py  → stats
        │
        ▼
dataset.json + stats.json + report.md + needs_ai_review.csv
        │
        ▼ (opcional)
ai_enrichment/enrichment_pipeline.py
  Claude haiku completa campos vacíos
  con confidence HIGH/MEDIUM/LOW
        │
        ▼
enriched_dataset.csv + suggested_values.csv

FLUJO DE REPORTE (para el jefe):

historial.json
        │
        ▼
historial_report.py (manual, sin IA)
        │
        ▼
historial_dataset.json + historial_report.md
        │
        ▼
analytics.html (dashboard visual)
        │
        ▼
analytics.pdf (para presentar)

FLUJO DE SYNC (historial al repositorio remoto):

POST /api/sync
        │
        ▼
servidor.py ejecuta:
  git add historial.json
  git commit
  git push
        │
        ▼
GitHub repo (kudelkacris/linkedin-hintmedia)
        │
        ▼
Cloudflare Pages (historial.pages.dev)
viewer.html lee historial.json desde GitHub
```

---

## 5. MODELO DE DATOS

### `historial.json`
Fuente de verdad operacional. **427 entradas** al 30/06/26.

| Campo | Tipo | Quién escribe | Quién modifica | Cuándo cambia |
|---|---|---|---|---|
| `id` | number (timestamp ms) | background.js / histUpsert | nunca | al crear |
| `date` | string DD/MM/YY | background.js / histUpsert | nunca | al crear |
| `name` | string | extensión (scraping) / usuario | nunca | al crear |
| `empresa` | string | regex en popup.js o servidor | usuario puede editar | al crear |
| `variantTitle` | string | usuario (elige variante) | nunca | al crear |
| `profileRaw` | string | extensión (scraping) / usuario pega | nunca | al crear (desde 18/06/26) |
| `msg1` | string | IA generada | nunca | al crear |
| `msg2` | string | IA generada | nunca | al crear |
| `extraMsgs` | object | IA generada especulativamente | nunca | al crear |
| `conversationHistory` | array | usuario (respuestas reales) | usuario agrega msgs | en cada interacción |
| `stage` | number 1-5 | usuario (botón avanzar stage) | usuario | en cada avance |
| `stageHistory` | array | automático al cambiar stage | nunca | en cada avance |
| `dossierMail` | boolean | usuario (checkbox) | usuario | cuando se envía dossier por mail |

**INCERTIDUMBRE:** No existe campo `profileRaw` en entradas anteriores al 18/06/26. Eso hace irrecuperables esos perfiles para análisis.

---

### `dataset_builder/outputs/dataset.json`
Dataset construido desde `conversaciones/*.md`. Estructura diferente al historial.

| Campo principal | Origen |
|---|---|
| `ID_CONVERSACION` | autogenerado CONV_XXXX |
| `PROSPECTO`, `EMPRESA`, `PAIS`, `SECTOR`, `CARGO` | bold fields del .md + fallback historial.json |
| `NIVEL_SENIORITY` | heurística por regex sobre CARGO |
| `VARIANTE_MSG1` | regex sobre texto de MSG1 |
| `RESPONDIO_MSG1` | presencia de texto en respuesta_msg1 |
| `DOSSIER_ENVIADO` | Estado raw + dossier_text + pidio_dossier |
| `ENGAGEMENT_LEVEL` | regex explícito en .md, fallback heurística por longitud/preguntas/emoji |
| `OBJECION_PRINCIPAL` | regex sobre señal del prospecto (nunca sobre nuestros msgs) |
| `RESULTADO_FINAL` | lógica cascada: CLIENTE > REUNION > SEGUIMIENTO > DOSSIER > SIN_RESPUESTA |
| `NEEDS_AI` | boolean: ¿algún campo crítico vacío? |

---

### `conversaciones/*.md`
Archivos de texto libre con formato semi-estructurado. **No hay schema estricto.**

Formato esperado:
```markdown
# Nombre Prospecto
**Empresa:** X
**Cargo:** Y
**País:** Z
**Sector:** W
**Estado:** dossier enviado

## MSG1
> burbuja 1
> burbuja 2
> burbuja 3

## Respuesta MSG1
> texto que respondió el prospecto

## MSG2
> burbuja 1
...

## SEG1
> burbuja 1
...

## Notas
texto libre
```

**PROBLEMA REAL:** El formato no siempre es consistente. `extractors.py` tiene lógica de fallback pero puede fallar con formatos no estándar.

---

## 6. AUTOMATIZACIONES

### Hace automáticamente el PROGRAMA (sin intervención humana):
- Parseo de respuesta de la API (regex sobre texto plano)
- Scoring de variantes (1-10, IA)
- Detección de la "mejor variante" (badge ⭐ en la UI)
- Upsert a `historial.json` con threading lock (evita corrupción en multi-tab)
- Extracción de empresa desde texto del perfil (regex simple)
- Panel "Próximos" (clasifica contactos por acción pendiente)
- Git push de historial.json (`/api/sync`)
- **Extensión:** Scraping del DOM de LinkedIn, envío de burbujas con delays random (4-6s), POST al historial tras envío

### Hace automáticamente CLAUDE (IA):
- Análisis estratégico del perfil (HECHOS → INTERPRETACIÓN → TENSIÓN → HIPÓTESIS)
- Generación de MSG1 variante A y C
- Generación especulativa de MSG2, MSG3, MSG4, SEG1, SEG2
- Scoring multidimensional (SIGNAL_QUALITY, PERSONALIZATION_DEPTH, HALLUCINATION_RISK, etc.)
- Clasificación del prospecto (PROFILE_TYPE, SENIORITY, DECISION_POWER, COMMERCIAL_RELEVANCE)
- Clasificación de ENGAGEMENT_LEVEL en `handleReply()`
- Sugerencia de respuesta contextual a cada mensaje del prospecto
- Generación de SEG1 real (con contexto completo de conversación) en `handleReply()`
- Enriquecimiento de campos vacíos del dataset (ai_enrichment)

### Hace el USUARIO manualmente:
- Copiar el perfil de LinkedIn y pegarlo en la web app
- Elegir variante (aunque el sistema sugiere la mejor)
- Copiar los mensajes y pegarlos en LinkedIn (en la web app)
- Copiar las respuestas del prospecto y pegarlas en el hilo
- Avanzar el stage en la UI
- Marcar dossier enviado
- Ejecutar los pipelines de análisis offline (`dataset_builder.py`, `historial_report.py`, `enrichment_pipeline.py`)
- Escribir los archivos `conversaciones/*.md` en sesiones con Claude Code
- Decidir si seguir o cerrar una conversación
- Enviar el dossier real (PDF) fuera del sistema

### Hace LINKEDIN:
- Entregar el mensaje al prospecto
- Mostrar si fue leído (lectura)
- Notificar al prospecto
- Entregar la respuesta del prospecto (que el usuario luego copia)

---

## 7. DECISIONES DEL SISTEMA

| Decisión | Datos que usa | Dónde está implementada | Reglas |
|---|---|---|---|
| Filtrar prospecto (APTO/DUDOSO/DESCARTAR) | Texto del perfil | SYSTEM prompt de index.html + popup.js | CEO buscando empleo, freelancer sin estructura, estudiante → DESCARTAR |
| Elegir variante A vs C | Señal humana disponible en el perfil | IA (SCORE 1-10 por variante) | A=señal personal, C=señal de trabajo. Si el perfil es escaso → D |
| Badge "mejor variante" | SCORE de cada variante | `renderVariants()` en index.html (~línea 1100) | max(score) = badge ⭐ |
| Elegir cliente Hint a mencionar en MSG2 | Sector del prospecto | SYSTEM prompt (CLAUDE.md + system) | Energía→TGS/Transener; Seguros→Libra/Destiny; Retail→Destiny/Tasarolli; etc. |
| Clasificar ENGAGEMENT_LEVEL | Texto de respuestas del prospecto + conversación | `detect_engagement()` en heuristics.py (regex explicit first, luego heurística longitud/pregunta/emoji) + `handleReply()` en index.html (IA) | HIGH: entusiasmo/preguntas/mail; MEDIUM: aceptación estándar; LOW: monosilábico |
| Modo de SEG1 | ENGAGEMENT_LEVEL | SYSTEM prompt de index.html (sección REGLAS SEGUIMIENTOS) | LOW→sin CTA; MEDIUM→CTA blando; HIGH→CTA directo |
| Detectar objeción | Texto de respuestas del prospecto (NUNCA nuestros mensajes) | `detect_objecion()` en heuristics.py | Regex por reglas: HAS_AGENCY, NO_BUDGET, BAD_TIMING, PARTNERSHIP, CURIOSITY_ONLY |
| Detectar sector | Nombre de empresa + cargo + texto del perfil | `detect_sector()` en heuristics.py (SECTOR_RULES en config.py) | 60+ empresas hardcodeadas por nombre + patrones regex de industria |
| Detectar resultado final | stage + respondió + dossier + SEG1 + SEG2 | `detect_resultado_final()` en heuristics.py | Cascada: CLIENTE > REUNION > SEGUIMIENTO > DOSSIER > SIN_RESPUESTA |
| Confianza del enrichment IA | Valor + evidencia citada + tipo de campo | `enrichment_validator.py` | HIGH/MEDIUM→aplicar; LOW→solo sugerir. Si valor no está en enum→descartar |

---

## 8. MÓDULOS EXISTENTES

### Funcionales y en uso activo:
- ✅ **MSG1 generación** — variantes A y C (web app). Variantes A y C (extensión). Framework HECHOS→INTERPRETACIÓN→TENSIÓN→HIPÓTESIS.
- ✅ **MSG2 generación** — 4 burbujas, se genera en `handleReply()` con contexto real de conversación.
- ✅ **SEG1 generación** — en `handleReply()` con ENGAGEMENT_LEVEL como input. Implementado en código.
- ✅ **Análisis estratégico** — 4 fases (HECHOS, INTERPRETACIÓN, TENSIÓN, HIPÓTESIS) visibles en la UI.
- ✅ **Scoring de variantes** — SCORE 1-10 por variante + badge mejor opción.
- ✅ **Scoring multidimensional** — SIGNAL_QUALITY, PERSONALIZATION_DEPTH, HALLUCINATION_RISK, GLOBAL_SCORE, RECOMMENDED_PRIORITY.
- ✅ **Profile classification** — PROFILE_TYPE, SENIORITY, DECISION_POWER, BUYING_ROLE, COMMERCIAL_RELEVANCE.
- ✅ **Confidence layer** — CONFIDENCE_LEVEL, SIGNAL_SOURCE, ALLOWED_FOR_MSG1.
- ✅ **Historial** — localStorage (web app) + historial.json (servidor). Upsert multi-pestaña.
- ✅ **Panel Próximos** — pipeline visual de quién necesita MSG2, dossier o seguimiento.
- ✅ **Extensión Chrome** — scraping automático + envío de burbujas con delays.
- ✅ **Dataset builder** — pipeline regex/heurísticas sobre conversaciones/*.md.
- ✅ **AI Enrichment** — enriquecimiento con confidence guardrails.
- ✅ **Analytics dashboard** — HTML estático para el jefe.
- ✅ **Historial report** — embudo completo desde historial.json.
- ✅ **Git sync** — push de historial.json al repo remoto desde la UI.
- ✅ **Viewer público** — historial.pages.dev, Cloudflare Pages.
- ✅ **Prompt caching** — activado en servidor.py (`cache_control: ephemeral`).

### Generados pero NO integrados al flujo real:
- ⚠️ **MSG3, MSG4, SEG2** — se generan especulativamente al inicio con el perfil crudo, sin contexto de conversación real. Los bloques `---MSG3---` etc. en el output de la IA son placeholders, no se usan downstream.
- ⚠️ **extraMsgs.SEG1** en historial.json — generado con perfil inicial, no refleja el SEG1 real enviado.

### Incompleto / sin uso downstream claro:
- ⚠️ **enriched_dataset.csv** — no está claro si se reintegra al dataset principal o si es solo para auditoría manual.
- ⚠️ **dossier_verification.py** — verifica si el dossier fue enviado según el .md, pero no está integrado al pipeline automático.
- ⚠️ **semantic_enrichment.py** — experimental, no es el flujo principal.

---

## 9. DEUDA TÉCNICA

### Crítica (afecta fiabilidad o escalabilidad):

**1. SYSTEM PROMPT DUPLICADO EN index.html**
El SYSTEM está definido dos veces: en `const SYSTEM` (~línea 396) y dentro del string del prompt en `generateOpeners()` (~línea 895). Si se actualiza uno y no el otro, el comportamiento es inconsistente. Esto ya ocurrió al menos una vez.

**2. SYSTEM PROMPT TRIPLICADO ENTRE ARCHIVOS**
`index.html` tiene su propio SYSTEM, `extension/popup.js` tiene otro SYSTEM (versión anterior, 2 variantes), y `ai_enrichment/enrichment_prompts.py` tiene el suyo. Tres versiones del mismo sistema de razonamiento, divergentes.

**3. MONOLITO index.html (2235 líneas)**
Todo el CSS, JS, HTML, SYSTEM prompt y lógica de negocio están en un solo archivo. Sin módulos, sin imports, sin bundler. Cualquier cambio requiere navegar manualmente el archivo. Alto riesgo de editar la parte equivocada.

**4. NO HAY SCHEMA ESTRICTO PARA conversaciones/*.md**
El parser en `extractors.py` hace lo mejor que puede con texto libre, pero la calidad del dataset depende de cuán bien fue escrito cada .md. Variaciones de formato generan campos vacíos en el dataset.

**5. SECTOR_RULES HARDCODEADA DE EMPRESAS INDIVIDUALES**
La detección de sector usa reglas con nombres de empresas específicas (Ecopetrol, Petrobras, Antofagasta Minerals...). Si llega un contacto de una empresa no registrada, el sector queda vacío. Actualmente 47% de los 427 contactos no tienen sector detectado.

**6. extraMsgs (SEG1/SEG2/MSG3/MSG4) ESPECULATIVOS**
Se generan al inicio con el perfil crudo, sin saber aún si el prospecto va a responder ni cómo. No tienen valor operacional real. El SEG1 real se genera en `handleReply()` con contexto completo.

**7. HISTORIAL.JSON COMO ÚNICO STORE SIN BACKUP AUTOMÁTICO**
`historial.json` es la única base de datos. El sync con git es manual (botón en UI). No hay backup automático. Si el archivo se corrompe o se borra, se pierde todo el historial.

**8. localStorage (web app) + historial.json COMO DOS FUENTES DE VERDAD**
La web app lee desde localStorage (`hm_hist_v2`) y sincroniza con el servidor. La extensión escribe directamente al servidor. Pueden existir entradas en localStorage que no están en historial.json y viceversa.

**9. FALTA DE TRACKING DE CONVERSIÓN FINAL**
Solo hay 2 reuniones confirmadas de 427 contactos, pero el sistema no trackea explícitamente cuántos SEG1 generaron respuesta ni cuántos dossiers derivaron en llamada. El `stage 5` del historial no equivale necesariamente a reunión.

**10. EXTENSIÓN: SYSTEM PROMPT DESINCRONIZADO**
`popup.js` tiene el SYSTEM de una versión anterior del proyecto (2 variantes, sin las 4 fases de análisis, sin el scoring multidimensional). Los resultados de la extensión son cualitativamente inferiores a los de la web app.

**11. NO HAY TESTS AUTOMATIZADOS**
Ningún test unitario, de integración, ni de regresión. Los cambios al SYSTEM prompt o a las reglas heurísticas no tienen validación automática.

**12. DEPENDENCIA ÚNICA: httpx**
`requirements.txt` tiene solo una dependencia. Positivo. Pero `httpx` no maneja reintentos automáticos. Si la API de Anthropic devuelve un 429 o 500, el servidor devuelve error al cliente sin retry.

**13. CÓDIGO DUPLICADO EN background.js Y content.js**
El código de `sendBubble` está escrito dos veces con pequeñas diferencias: en `content.js` (vía mensajes Chrome) y en `background.js` (vía scripting.executeScript). El background.js es el que se usa realmente; el de content.js es un fallback o remanente.

---

## 10. PUNTOS DE ENTRADA

### Archivos que el USUARIO ejecuta directamente:
| Archivo | Cómo | Cuándo |
|---|---|---|
| `servidor.py` | `python servidor.py` | Siempre que se quiere usar la web app o la extensión |
| `dataset_builder/dataset_builder.py` | `python dataset_builder/dataset_builder.py` | Cuando se quiere reconstruir el dataset desde las .md |
| `dataset_builder/historial_report.py` | `python dataset_builder/historial_report.py` | Para generar el reporte del embudo desde historial.json |
| `ai_enrichment/enrichment_pipeline.py` | `python ai_enrichment/enrichment_pipeline.py --limit N` | Cuando se quiere enriquecer campos vacíos con IA |

### Archivos que ejecutan OTROS SCRIPTS (no directamente):
| Archivo | Quién lo llama |
|---|---|
| `dataset_builder/config.py` | dataset_builder.py, heuristics.py, historial_report.py, enrichment_pipeline.py |
| `dataset_builder/extractors.py` | dataset_builder.py |
| `dataset_builder/heuristics.py` | dataset_builder.py, historial_report.py |
| `dataset_builder/analytics.py` | dataset_builder.py |
| `ai_enrichment/enrichment_prompts.py` | enrichment_pipeline.py |
| `ai_enrichment/enrichment_validator.py` | enrichment_pipeline.py |
| `ai_enrichment/confidence_engine.py` | enrichment_validator.py (probablemente) |
| `index.html` | servidor.py lo sirve al browser |

### Archivos que NUNCA se ejecutan directamente:
- `analytics.html` — se abre en browser
- `viewer.html` — se abre en browser o está en Cloudflare Pages
- `extension/content.js` — se inyecta automáticamente en LinkedIn (manifest)
- `extension/background.js` — se activa como service worker
- `extension/popup.js` — se carga al abrir el popup de la extensión
- `ai_enrichment/build_audit_sample.py`, `compute_precision.py`, `conversion_report.py` — scripts de auditoría one-shot, ejecutados manualmente en contexto puntual

---

## 11. ROADMAP HISTÓRICO (reconstruido desde código y git)

### Fase 1 — Generador de mensajes (mayo 2026)
- `index.html` + `servidor.py` básico
- MSG1 con variantes A/C, framework inicial (TRABAJO → RESPONSABILIDAD → HINT)
- Historial en localStorage
- Sin extensión

### Fase 2 — Extensión Chrome (mayo-junio 2026)
- `extension/` creada
- Scraping automático del perfil
- Envío automático de burbujas con delays
- El SYSTEM de la extensión es una copia del index.html de ese momento (más simple)

### Fase 3 — Historial persistente + sync (junio 2026)
- `servidor.py` agrega endpoint `/api/historial` (POST upsert con threading lock)
- `/api/sync` para git push
- Historial migrado de solo localStorage a servidor
- `viewer.html` + Cloudflare Pages

### Fase 4 — Enriquecimiento metodológico (09-18/06/26)
- SYSTEM prompt evoluciona: SEÑAL HUMANA, diferenciación A vs C, etapa de interpretación
- MSG2 framework 4 pasos (HECHO → COMPLEJIDAD → OPORTUNIDAD → HINT)
- SEG1 metodología 6 líneas + ENGAGEMENT_LEVEL
- Filtro APTO/DUDOSO/DESCARTAR
- profileRaw empieza a guardarse (18/06/26)

### Fase 5 — Dataset builder + AI Enrichment (junio 2026)
- `dataset_builder/` creado: pipeline regex para conversaciones/*.md
- `ai_enrichment/` creado: enriquecimiento con guardrails
- `conversaciones/` empieza a poblarse sistemáticamente
- Análisis de objeciones, engagement, variantes

### Fase 6 — Análisis estratégico profundo (jun 2026)
- SYSTEM evoluciona a 4 fases: HECHOS → INTERPRETACIÓN → TENSIÓN → HIPÓTESIS
- Confidence layer (FASE 2), Profile classification (FASE 3), Scoring multidimensional (FASE 4)
- Columnas de Seguimiento 1/2 en la UI
- Panel "Próximos" en index.html

### Fase 7 — Analytics + Reporting (29/06/26)
- `historial_report.py` para embudo desde historial.json
- `analytics.html` dashboard para el jefe
- SECTOR_RULES expandido: cobertura 26% → 53%
- Análisis estadístico: variante A > C, CEO peor target, sectores 0%

---

## 12. ESTADO ACTUAL (30/06/2026)

### ¿Qué es hoy este proyecto?

**Es un sistema híbrido en la frontera entre CRM y plataforma de inteligencia comercial.** No encaja perfectamente en ninguna categoría existente.

| Dimensión | Estado real |
|---|---|
| Generador de mensajes | ✅ Maduro. Metodología iterada 7+ veces. Funciona. |
| CRM básico | ✅ Parcial. Historial con stages, próximos, tracking de dossiers. Sin CRM completo. |
| Sistema de inteligencia | 🟡 En construcción. Dataset, enrichment, analytics existen pero no están integrados en un loop. |
| Automatización | 🟡 Parcial. Extensión automatiza envío. Análisis sigue siendo manual. |
| Plataforma de aprendizaje | 🔴 Incipiente. Los datos existen pero no retroalimentan automáticamente el sistema. |

### Métricas reales al 30/06/26:
- 427 contactos en historial.json
- 107/427 = 25.1% conversión a dossier
- 2 reuniones confirmadas (0.47%)
- Costo por contacto completo: ~$0.004 USD
- Sector con mejor conversión: Real Estate / Educación / Minería (~35%)
- Peor target: CEO en frío (10% vs 27% Director)
- Variante A supera Variante C (28.5% vs 19.4%)

### Fortalezas reales:
1. La metodología de mensajes está bien iterada y funciona
2. El servidor es simple y confiable para uso individual
3. Los pipelines de análisis producen insights accionables
4. El costo de operación es negligible (~$0.40 por 100 nuevos contactos)

### Limitaciones reales:
1. No escala más allá de 1 usuario (Florencia) sin refactoring mayor
2. No hay loop de retroalimentación automático: los datos no mejoran la generación
3. El SYSTEM prompt no sabe nada de los patrones aprendidos de los 427 contactos
4. La conversión final (dossier → reunión) no está trackeada de forma confiable

---

## 13. VISIÓN A FUTURO (24 meses, perspectiva CTO)

Este sistema tiene una oportunidad real de convertirse en **la primera plataforma de inteligencia comercial B2B especializada en agencias de comunicación latinoamericanas**. Pero para llegar ahí hay que resolver primero la arquitectura base y luego construir encima.

### Etapa 1 — Estabilización (meses 1-3): "Hacer lo que hace, bien"

**Problema central hoy:** los datos y la generación son silos. El sistema aprende implícitamente (via memoria humana en sesiones con Claude) pero no aprende automáticamente.

**Lo que haría:**
- Separar el SYSTEM prompt en un archivo `.md` versionable, único, que todos los clientes (web, extensión, enrichment) consumen. Fin de la triplicación.
- Migrar de `historial.json` a SQLite local. Mantener simplicidad pero ganar queries.
- Crear un schema estricto para `conversaciones/*.md` y un validator al guardar.
- Unificar el tracking de conversión: dossier → respuesta a dossier → reunión → cliente. Cada stage documentado con fecha.

### Etapa 2 — El loop de aprendizaje (meses 3-8): "Los datos mejoran la generación"

**Problema central:** el SYSTEM prompt genera mensajes sin saber que en Real Estate se convierte al 37% y en Logística al 0%. Ese conocimiento está en el dataset pero no llega al modelo.

**Lo que haría:**
- Construir un módulo de `context injection`: antes de cada generación, inyectar en el prompt los top-3 sectores del prospecto con sus tasas de conversión reales, las objeciones más frecuentes de ese sector, y el ENGAGEMENT promedio de perfiles similares.
- Implementar un sistema de etiquetado post-conversación: el usuario marca qué funcionó y qué no. Eso alimenta directamente las reglas del SYSTEM.
- Detectar automáticamente el sector del prospecto al pegar el perfil (usa el mismo regex del dataset_builder) y mostrar el dato antes de generar.

### Etapa 3 — Plataforma multi-usuario (meses 6-14): "De uso individual a equipo"

**Hoy:** un usuario, un servidor local, un archivo JSON.

**Lo que haría:**
- Migrar servidor.py a un backend real (FastAPI + PostgreSQL) deployado en la nube.
- Sistema de autenticación simple (un login por agencia).
- Historial compartido entre el equipo de Hint Media.
- Cloudflare Workers o similar para la extensión, sin depender de localhost.
- API key de Anthropic centralizada, sin estar en .env.local de cada máquina.

### Etapa 4 — Inteligencia proactiva (meses 12-24): "El sistema trabaja solo"

**La visión real:** el sistema identifica cuándo contactar, a quién, con qué mensaje, y trackea el resultado sin intervención manual.

**Lo que haría:**
- Scraping periódico de perfiles ya contactados: si el prospecto publicó algo nuevo, disparar alerta.
- Scoring de prioridad automático: dados 10 perfiles nuevos, ranquear cuál tiene mayor probabilidad de llegar a dossier basado en los 427 casos históricos.
- Pipeline de seguimiento automático: SEG1 se sugiere automáticamente a los N días de enviado el dossier, sin que el usuario tenga que recordarlo.
- A/B testing sistemático: cuando hay ambigüedad entre variante A y C, trackear cuál convirtió y alimentar el scoring.
- Detección de patterns: "los prospectos de Educación que responden con pregunta en el MSG1 tienen 60% de probabilidad de llegar a reunión" → el sistema lo sabe y lo muestra.

### Lo que NO haría en 24 meses:
- Integración directa con LinkedIn API (Terms of Service, riesgo de banning)
- Envío masivo automatizado sin revisión humana (kill la personalización que hace funcionar el sistema)
- Reemplazar a Claude con un modelo propio (el moat está en la metodología, no en el modelo)

### La arquitectura objetivo en 24 meses:

```
[Extensión Chrome] ──► [Backend FastAPI/Cloud]
[Web App React]  ──►        │
                            ├─ PostgreSQL (historial, conversaciones, analytics)
                            ├─ Anthropic API (generación + enrichment)
                            ├─ Sistema de reglas (SYSTEM versionable)
                            ├─ Context Injector (stats → prompt)
                            └─ Dashboard (analytics en tiempo real)
                                │
                                ▼
                        [Loop de aprendizaje]
                        datos reales → mejoran generación
                        generación mejora → más dossiers
                        más dossiers → más datos
```

El sistema no reemplaza a la persona que vende. La hace exponencialmente más efectiva. Ese es el producto.

---

*Documento generado por auditoría CTO el 30/06/2026. Basado exclusivamente en lectura de código, archivos de datos y memoria del proyecto. Nada fue inferido sin evidencia directa en el código.*
