# HINT INTELLIGENCE ENGINE
## Diseño Arquitectural · Versión 1.0 · 30/06/2026

> "El sistema no debe recordar lo que pasó. Debe entender por qué pasó y predecir qué va a pasar."

---

## 1. VISIÓN GENERAL

El Hint Intelligence Engine (HIE) es la capa cerebral del sistema. No genera mensajes. No parsea perfiles. No hace dashboards.

**Su única función es convertir conversaciones pasadas en ventaja competitiva futura.**

Cada vez que una conversación nueva entra al sistema, el HIE la compara con todo lo que pasó antes. Detecta si algo cambió. Actualiza lo que sabe. Y recomienda qué hacer diferente la próxima vez.

El resultado concreto es uno solo: **más reuniones, con menos intentos, con prospectos mejores.**

---

## 2. OBJETIVO

El sistema hoy genera mensajes correctos para un prospecto puntual.

El HIE genera conocimiento correcto sobre **clases de prospectos**, **patrones de mercado** y **estrategias que funcionan**.

La diferencia:

| Sistema actual | HIE |
|---|---|
| "Generá un MSG1 para esta persona" | "Para perfiles como este, la variante A convierte 31%, la C convierte 19%. Usá A." |
| "¿Qué sectores tenemos?" | "Retail bajó de 15% a 8% en los últimos 30 días. Algo cambió. Revisá el mensaje." |
| "¿Cuántos dossiers mandamos?" | "Los dossiers mandados a CEOs de tecnología en frío tienen 0% de conversión a reunión. Pará de mandarlos." |
| Datos históricos estáticos | Conocimiento que se actualiza solo |

---

## 3. FILOSOFÍA

### El HIE piensa como un científico, no como un consultor.

Un consultor inventa hipótesis y las presenta con confianza.
Un científico observa, mide, compara, y solo concluye cuando tiene evidencia suficiente.

**Reglas filosóficas no negociables:**

**1. Toda conclusión tiene evidencia o no existe.**
Cada insight del HIE incluye: cuántos casos lo respaldan, qué datos específicos lo confirman, y cuánta confianza merece.

**2. Sin evidencia suficiente, el sistema dice "no sé" en vez de inventar.**
N < 10 casos = insight marcado como "DATOS INSUFICIENTES". No se presenta como conclusión.

**3. Correlación no es causalidad.**
El HIE detecta patrones. No afirma causas. Si Real Estate convierte más, lo dice. Por qué convierte más, lo deja como hipótesis para que el humano verifique.

**4. Lo que no mejora conversión a reunión no se construye.**
Cada módulo, cada análisis, cada output del HIE debe poder responder: "¿esto aumenta la probabilidad de conseguir más reuniones con mejores clientes?" Si la respuesta no es clara, el módulo no se construye.

**5. El HIE no reemplaza el juicio humano. Lo informa.**
El HIE sugiere. Florencia decide. El sistema aprende de lo que Florencia decide.

---

## 4. ARQUITECTURA CONCEPTUAL

```
╔══════════════════════════════════════════════════════════════╗
║                   HINT INTELLIGENCE ENGINE                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   FUENTES DE DATOS          MOTORES DE ANÁLISIS              ║
║   ┌──────────────┐          ┌──────────────────────┐         ║
║   │historial.json│──────►   │  pattern_engine      │         ║
║   │  427 entries │          │  (patrones estáticos) │         ║
║   └──────────────┘          └──────────┬───────────┘         ║
║                                        │                     ║
║   ┌──────────────┐          ┌──────────▼───────────┐         ║
║   │conversaciones│──────►   │  conversation_engine │         ║
║   │   /*.md      │          │  (señales en texto)  │         ║
║   └──────────────┘          └──────────┬───────────┘         ║
║                                        │                     ║
║   ┌──────────────┐          ┌──────────▼───────────┐         ║
║   │ dataset.json │──────►   │  change_detector     │         ║
║   │historial_ds  │          │  (qué cambió)        │         ║
║   └──────────────┘          └──────────┬───────────┘         ║
║                                        │                     ║
║   ┌──────────────┐          ┌──────────▼───────────┐         ║
║   │enriched_ds   │──────►   │  knowledge_base      │         ║
║   │stats.json    │          │  (lo que sabe el     │         ║
║   └──────────────┘          │   sistema)           │         ║
║                             └──────────┬───────────┘         ║
║                                        │                     ║
║                             ┌──────────▼───────────┐         ║
║                             │  recommendation      │         ║
║                             │  _engine             │         ║
║                             │  (qué hacer ahora)   │         ║
║                             └──────────┬───────────┘         ║
║                                        │                     ║
║   SALIDAS                   ┌──────────▼───────────┐         ║
║   ┌──────────────┐          │  experiment_engine   │         ║
║   │intelligence  │◄─────────│  (qué testear)       │         ║
║   │_report.md    │          └──────────────────────┘         ║
║   │              │                                           ║
║   │context_      │                                           ║
║   │injection.json│          ┌──────────────────────┐         ║
║   │              │◄─────────│  prediction_engine   │         ║
║   │experiments   │          │  (FASE 6 — futuro)   │         ║
║   │_queue.json   │          └──────────────────────┘         ║
║   └──────────────┘                                           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 5. MÓDULOS

### MÓDULO 1: `pattern_engine`
**Misión:** Encontrar qué combinaciones de variables predicen conversión.

**Qué analiza:**
- Sector × resultado (dossier, reunión, silencio)
- Variante MSG1 × resultado
- Seniority × resultado
- Sector × Seniority × resultado (combos)
- Tipo de objeción × resultado posterior
- ENGAGEMENT_LEVEL × resultado

**Qué produce:**
```json
{
  "insight_id": "PI_001",
  "tipo": "CONVERSION_PATTERN",
  "titulo": "Real Estate convierte al 37.5% a dossier",
  "evidencia": "3 de 8 contactos en Real Estate llegaron a dossier",
  "n_casos": 8,
  "confianza": "BAJA",
  "confianza_reason": "n < 15, no concluyente",
  "accion_recomendada": "Aumentar volumen en Real Estate para confirmar",
  "impacto_comercial": "MEDIO",
  "fecha_detectado": "2026-06-30"
}
```

**Regla de confianza:**
- n < 10: INSUFICIENTE (no se presenta como conclusión)
- n 10-30: BAJA (se presenta como hipótesis)
- n 31-100: MEDIA (se presenta como patrón)
- n > 100: ALTA (se presenta como regla)

---

### MÓDULO 2: `conversation_engine`
**Misión:** Analizar el texto de las conversaciones reales para encontrar señales lingüísticas que predicen conversión.

**Fuente de datos clave:** `conversationHistory` en historial.json. Cada entrada tiene el hilo completo: mensajes enviados + respuestas del prospecto.

**Qué analiza:**
- ¿Qué palabras usa el prospecto cuando responde y luego acepta el dossier?
- ¿Qué palabras usa cuando luego rechaza?
- ¿Cuánto tarda en responder (cuando hay timestamps)?
- ¿Cuánto texto escribe en la respuesta?
- ¿Hace preguntas? ¿Cuántas?
- ¿Qué dice específicamente al responder al MSG1 que predice que va a pedir el dossier?

**Qué produce:**
```json
{
  "insight_id": "CE_001",
  "tipo": "SIGNAL_PATTERN",
  "titulo": "Respuestas con '?' en la primera respuesta → 78% convierte a dossier",
  "evidencia": "14 de 18 conversaciones donde el prospecto hizo una pregunta en su primera respuesta terminaron en dossier",
  "n_casos": 18,
  "confianza": "MEDIA",
  "señal_detectada": "pregunta en respuesta_msg1",
  "accion_recomendada": "Cuando el prospecto responde con pregunta, priorizar como HIGH y responder con urgencia"
}
```

**INCERTIDUMBRE REAL ACTUAL:** Este análisis requiere que `conversationHistory` tenga las respuestas del prospecto bien cargadas. Hoy la calidad de ese campo varía. El conversation_engine necesita primero auditar la completitud del campo antes de sacar conclusiones.

---

### MÓDULO 3: `change_detector`
**Misión:** Detectar automáticamente cuando algo cambia respecto al período anterior.

Este es el módulo más valioso para operaciones diarias. Sin él, los cambios de mercado se descubren semanas después.

**Qué monitorea:**
- Tasa de dossier por sector (mes a mes)
- Distribución de objeciones (crecen las de "ya tenemos agencia"?)
- ENGAGEMENT_LEVEL promedio de nuevos contactos
- Rendimiento de Variante A vs C en los últimos 30 días
- Tasa de respuesta a MSG1 (¿está bajando?)
- Tasa de conversión dossier → respuesta al dossier
- Nuevos sectores que aparecen en el pipeline

**Cómo detecta cambios:**
Compara ventanas de tiempo: últimos 30 días vs los 30 días anteriores. Si la diferencia supera un umbral (configurable, default: 10 puntos porcentuales con n > 5 en ambos períodos), genera una alerta.

**Qué produce:**
```json
{
  "alerta_id": "CD_001",
  "tipo": "TREND_CHANGE",
  "severidad": "ALTA",
  "titulo": "Retail/Consumo: caída de 12% a 0% en los últimos 30 días",
  "periodo_anterior": { "n": 8, "dossier_rate": "12.5%" },
  "periodo_actual": { "n": 5, "dossier_rate": "0%" },
  "hipotesis_posibles": [
    "El mensaje no resuena con el sector actualmente",
    "Los perfiles contactados en Retail cambiaron de seniority",
    "El contexto de mercado del sector cambió"
  ],
  "accion_recomendada": "Revisar los 5 contactos de Retail de este mes. Identificar qué tiene en común el rechazo.",
  "fecha_detectada": "2026-06-30"
}
```

**Problema actual:** El historial.json no tiene timestamps granulares por stage. Solo `date` al crear. Para hacer análisis temporal necesitamos `stageHistory[].date` que sí existe. El change_detector debe usar `stageHistory` para reconstruir cuándo llegó a cada etapa.

---

### MÓDULO 4: `knowledge_base`
**Misión:** Almacenar el conocimiento acumulado del sistema de forma estructurada y versionada.

No es una base de datos de conversaciones. Es una base de datos de **conocimiento extraído** de esas conversaciones.

**Estructura:**

```
hint_intelligence/
├── knowledge_base/
│   ├── patterns.json          # patrones de conversión detectados
│   ├── signals.json           # señales lingüísticas que predicen respuesta
│   ├── sector_intelligence.json  # lo que sabe el sistema de cada sector
│   ├── objection_playbook.json   # objeciones y qué hacer con cada una
│   ├── profile_archetypes.json   # arquetipos de prospectos (características comunes)
│   └── experiment_history.json   # experimentos propuestos, estado, resultado
```

**Ejemplo de `sector_intelligence.json`:**
```json
{
  "Real Estate": {
    "n_total": 8,
    "dossier_rate": 0.375,
    "confianza": "BAJA",
    "mejor_variante": "INSUFICIENTE",
    "mejor_seniority": "INSUFICIENTE",
    "objeciones_frecuentes": [],
    "señales_positivas": ["menciona expansión", "rol de marketing/comunicación propio"],
    "señales_negativas": [],
    "notas_estrategicas": "Sector con pocos casos. Priorizar para aumentar muestra.",
    "ultima_actualizacion": "2026-06-30",
    "version": 1
  },
  "Energía": {
    "n_total": 26,
    "dossier_rate": 0.269,
    "confianza": "MEDIA",
    "mejor_variante": "A",
    "mejor_seniority": "DIRECTOR",
    "objeciones_frecuentes": ["HAS_AGENCY", "BAD_TIMING"],
    "señales_positivas": ["publicaciones sobre transición energética", "menciona comunicación corporativa"],
    "señales_negativas": ["cargo muy técnico (ingeniero sin área de comunicación)"],
    "notas_estrategicas": "Mayor volumen absoluto. TGS/Transener como casos de referencia son muy efectivos.",
    "ultima_actualizacion": "2026-06-30",
    "version": 3
  }
}
```

**Regla crítica:** La knowledge_base no se reescribe. Se **versiona**. Cada actualización agrega `version + 1`. Esto permite ver cómo evolucionó el conocimiento del sistema.

---

### MÓDULO 5: `recommendation_engine`
**Misión:** Para un nuevo prospecto, recomendar la estrategia óptima basada en todo el conocimiento acumulado.

Este módulo se activa ANTES de generar el MSG1. Enriquece el contexto que recibe la IA.

**Input:** Sector del prospecto + Seniority + señales del perfil

**Output (context_injection):**
```json
{
  "prospecto": "Juan García",
  "sector": "Energía",
  "seniority": "DIRECTOR",
  "contexto_historico": {
    "conversion_rate_sector": "26.9%",
    "conversion_rate_sector_seniority": "27.3%",
    "confianza": "MEDIA",
    "variante_recomendada": "A",
    "cliente_referencia_recomendado": "TGS o Transener",
    "señales_positivas_a_buscar": [
      "publicaciones sobre transición energética",
      "menciona comunicación corporativa",
      "rol con audiencias externas"
    ],
    "objeciones_probables": ["HAS_AGENCY (40% de los casos)", "BAD_TIMING (20%)"],
    "alerta_especial": null,
    "n_casos_base": 26
  }
}
```

Este JSON se inyecta en el SYSTEM prompt como contexto adicional al momento de generar. La IA no inventa "cuál sector convierte más" — lo sabe porque el sistema se lo dice.

**IMPACTO COMERCIAL DIRECTO:** Si la IA sabe que para Energía + Director la variante A tiene 27% de conversión y la C tiene X%, puede tomar decisiones informadas en vez de estadísticas. Esto es el loop de aprendizaje que hoy no existe.

---

### MÓDULO 6: `experiment_engine`
**Misión:** Identificar qué no se sabe con suficiente certeza y proponer experimentos para saberlo.

El sistema hoy tiene sesgos de confirmación: si Variante A funcionó primero, se usó más, y los datos parecen confirmar que funciona. Pero el test no fue controlado.

**Qué detecta:**
- Variables con n insuficiente para conclusión (n < 30)
- Hipótesis plausibles que no han sido testeadas
- Variables que el sistema usa pero nunca ha validado

**Qué produce:**
```json
{
  "experimento_id": "EXP_001",
  "estado": "PENDIENTE",
  "hipotesis": "Variante C puede superar a Variante A en perfiles con señal de TRABAJO fuerte",
  "por_que": "Variante C solo tiene 67 casos (vs 260 de A). La diferencia estadística puede ser ruido.",
  "como_testear": "Para los próximos 20 prospectos con señal clara de trabajo (proyecto, expansión, operación), usar Variante C exclusivamente. Comparar tasa de dossier.",
  "n_minimo_para_conclusion": 20,
  "n_actual": 0,
  "resultado": null,
  "prioridad": "ALTA",
  "impacto_si_confirma": "Podría aumentar conversión en perfiles de trabajo de 19.4% a potencialmente 28%+",
  "riesgo": "Sacrificamos conversión en 20 prospectos si la hipótesis es falsa"
}
```

**Regla crítica:** El experiment_engine no ejecuta los experimentos. Los propone. Florencia decide si hacer el test o no. Cuando termina el test, registra el resultado y el knowledge_base se actualiza.

---

### MÓDULO 7: `strategy_engine`
**Misión:** Síntesis estratégica. Leer todo el conocimiento acumulado y producir recomendaciones de alto nivel sobre dónde invertir el tiempo de outreach.

**Qué produce (semanal o mensual):**

```
HINT INTELLIGENCE — ESTRATEGIA OUTBOUND · Semana 27/2026

PRIORIDAD 1 — SECTORES A ATACAR:
  Real Estate: 37.5% dossier (n=8, confianza BAJA → necesitamos más datos)
  Educación: 35.7% dossier (n=42, confianza MEDIA)
  Minería: 35.7% dossier (n=14, confianza MEDIA)

EVITAR ESTA SEMANA:
  Logística: 0/4 dossiers (n insuficiente, pero señal negativa)
  CEO en frío: 10% vs 27% Director — no es el momento

ALERTA ACTIVA:
  Retail pasó de 12.5% a 0% en los últimos 30 días.
  Revisar conversaciones recientes de Retail.

EXPERIMENTO EN CURSO:
  EXP_001 — Variante C en perfiles con señal de trabajo.
  Estado: 5/20 casos completados. Sin conclusión todavía.

RECOMENDACIÓN DE TARGETING ESTA SEMANA:
  Buscar: Educación / Minería / Real Estate
  Seniority objetivo: Director o Manager (evitar CEO en apertura fría)
  Variante default: A (28.5% vs 19.4% de C)
```

---

## 6. FLUJO COMPLETO DEL ENGINE

```
TRIGGER (manual o automático)
        │
        ▼
╔══════════════════════════════════╗
║  FASE 1: RECOLECCIÓN DE DATOS    ║
║  Lee todos los sources:          ║
║  - historial.json                ║
║  - dataset_builder/outputs/      ║
║  - ai_enrichment/outputs/        ║
║  - conversaciones/*.md           ║
║  Valida: ¿hay datos nuevos       ║
║  desde la última corrida?        ║
╚══════════════╤═══════════════════╝
               │
               ▼
╔══════════════════════════════════╗
║  FASE 2: ANÁLISIS                ║
║  pattern_engine → patrones       ║
║  conversation_engine → señales   ║
║  change_detector → alertas       ║
║  Cada módulo produce insights    ║
║  con n_casos y confianza         ║
╚══════════════╤═══════════════════╝
               │
               ▼
╔══════════════════════════════════╗
║  FASE 3: ACTUALIZACIÓN KB        ║
║  knowledge_base.update()         ║
║  Compara insights nuevos vs      ║
║  versión anterior.               ║
║  Si cambia algo → version++      ║
║  Si se confirma → confianza++    ║
║  Si contradice → flag manual     ║
╚══════════════╤═══════════════════╝
               │
               ▼
╔══════════════════════════════════╗
║  FASE 4: RECOMENDACIONES         ║
║  recommendation_engine           ║
║  experiment_engine               ║
║  strategy_engine                 ║
╚══════════════╤═══════════════════╝
               │
               ▼
╔══════════════════════════════════╗
║  FASE 5: OUTPUTS                 ║
║  intelligence_report.md          ║
║  context_injection.json          ║
║  experiments_queue.json          ║
║  alerts.json                     ║
╚══════════════╤═══════════════════╝
               │
               ├──► index.html lee context_injection.json
               │    y lo agrega al prompt antes de generar
               │
               ├──► estrategia_semanal.md para el jefe
               │
               └──► alerts.json muestra alertas en la UI
```

---

## 7. QUÉ DATOS CONSUME

| Fuente | Qué toma | Para qué |
|---|---|---|
| `historial.json` | stage, conversationHistory, variantTitle, msg1, msg2, empresa, date, stageHistory | Base principal de conversaciones y resultados |
| `dataset_builder/outputs/historial_dataset.json` | SECTOR, SENIORITY, VARIANTE, DOSSIER_ENVIADO, RESULTADO, RESPONDIO, N_RESPUESTAS | Dataset estructurado para análisis estadístico |
| `dataset_builder/outputs/dataset.json` | ENGAGEMENT_LEVEL, OBJECION_PRINCIPAL, VARIANTE_MSG1, RESULTADO_FINAL, MSG1, MSG2 | Dataset enriquecido desde conversaciones/.md |
| `dataset_builder/outputs/stats.json` | distribuciones, tasas de conversión históricas | Baseline para detección de cambios |
| `ai_enrichment/outputs/enriched_dataset.csv` | campos completados por IA con HIGH/MEDIUM confidence | Completar huecos en el análisis |
| `conversaciones/*.md` | texto completo de conversaciones individuales | Análisis lingüístico de señales |

**Qué NO consume (y por qué):**
- `suggested_values.csv` (LOW confidence — no es evidencia confiable)
- `extraMsgs` de historial.json (especulativos, no reflejan lo que se envió realmente)
- Archivos de presentaciones (no son datos estructurados)

---

## 8. QUÉ DATOS GENERA

```
hint_intelligence/
├── knowledge_base/
│   ├── patterns.json              # patrones con n_casos y confianza
│   ├── signals.json               # señales lingüísticas que predicen
│   ├── sector_intelligence.json   # inteligencia por sector
│   ├── objection_playbook.json    # qué hacer con cada objeción
│   ├── profile_archetypes.json    # arquetipos de prospectos que convierten
│   └── experiment_history.json    # historial de experimentos
│
├── outputs/
│   ├── intelligence_report.md     # reporte legible por humanos
│   ├── context_injection.json     # input para el SYSTEM prompt en tiempo real
│   ├── experiments_queue.json     # cola de experimentos pendientes
│   ├── alerts.json                # alertas de cambios detectados
│   └── strategy_brief.md         # recomendación estratégica semanal
│
└── engine_log.json                # registro de corridas, n_datos_procesados, cambios detectados
```

---

## 9. QUÉ APRENDE

Con el tiempo, el HIE construye conocimiento en estas dimensiones:

### 9.1. Conocimiento de sectores
- Cuáles convierten y en qué rango de fechas
- Cuáles tienen más objeciones específicas
- Qué clientes de referencia resuenan más en cada sector
- Qué cambios estacionales existen

### 9.2. Conocimiento de señales
- Qué tipo de señal humana en el perfil predice mejor respuesta
- Qué longitud de MSG1 funciona mejor
- Qué patrones en las respuestas del prospecto predicen que va a pedir el dossier
- Qué dice el prospecto que señala cierre inminente vs rechazo inminente

### 9.3. Conocimiento de timing
- Cuántos días entre MSG1 y respuesta en los casos que convirtieron
- Cuántos días óptimos esperar antes de enviar SEG1
- En qué días/momentos del mes hay más respuestas

### 9.4. Conocimiento de objeciones
- Cuáles objeciones son recuperables (HAS_AGENCY puede ser "dame más info igual")
- Cuáles son definitivas (HARD_NO)
- Qué mensaje de respuesta a objeción funciona mejor

### 9.5. Conocimiento de prospectos que llegan a reunión
- Características comunes de los 2 contactos que llegaron a reunión (Luis Pérez, Keylin Smith)
- Qué señales tenían sus perfiles que los hacían distintos
- Qué trayectoria siguió la conversación

---

## 10. QUÉ RECOMIENDA

El HIE produce recomendaciones en 4 niveles:

### NIVEL 1 — Recomendaciones de targeting (quién contactar)
> "Esta semana atacar Educación y Minería. Evitar Logística y CEO en frío."

### NIVEL 2 — Recomendaciones de mensaje (cómo contactar)
> "Para este perfil: Director de Comunicaciones en Energía, usar Variante A. Mencionar TGS o Transener. La señal de tensión que más resuena en este sector es 'coordinar intereses distintos alrededor de una narrativa'."

### NIVEL 3 — Recomendaciones de seguimiento (cuándo y cómo)
> "Este prospecto respondió con pregunta en su primera respuesta (HIGH engagement). No esperar. Responder hoy. La probabilidad de dossier con respuesta rápida es 78% (n=14)."

### NIVEL 4 — Recomendaciones de sistema (qué mejorar)
> "El SYSTEM prompt dice que Variante C es 'el trabajo'. Pero los datos muestran que las variantes etiquetadas C que mencionan un logro específico convierten 26% vs 14% cuando no lo mencionan. Considerar ajustar la definición de Variante C."

---

## 11. QUÉ NUNCA DEBERÍA HACER

**1. Inventar patrones donde no hay datos.**
Si n < 10, el HIE dice "insuficiente" y recomienda aumentar el volumen, no saca conclusiones.

**2. Modificar el SYSTEM prompt automáticamente.**
El HIE recomienda cambios. Un humano los valida y aplica. El sistema nunca reescribe sus propias instrucciones sin revisión humana.

**3. Bloquear o descartar prospectos automáticamente.**
Puede recomendar prioridades. No puede decidir "no contactar" sin que un humano lo vea.

**4. Atribuir causalidad a correlaciones.**
Si CEOs convierten menos, el HIE dice eso. No dice "porque los CEOs no tienen tiempo". La causa la investiga el humano.

**5. Contradecirse sin señalarlo.**
Si en una corrida el sector Retail muestra 0% y en la siguiente muestra 15%, el HIE lo señala como inconsistencia (probablemente hay pocos datos) en vez de silenciosamente cambiar su recomendación.

**6. Optimizar métricas intermedias en vez del objetivo final.**
El objetivo es reuniones, no dossiers. El HIE no puede recomendar estrategias que maximizan dossiers pero matan conversiones a reunión.

**7. Generar reportes largos que nadie lee.**
Cada output del HIE tiene un formato corto y accionable. Si algo no lleva a una acción concreta, no se incluye.

---

## 12. ROADMAP POR FASES

---

### FASE 1 — OBSERVACIÓN
**"El sistema empieza a saber lo que tiene"**

**¿Qué aporta?**
El HIE lee todos los datos existentes, los organiza y produce la primera versión de la `knowledge_base`. Establece el baseline contra el cual se van a medir todos los cambios futuros.

**Módulos de esta fase:**
- `pattern_engine` (versión básica: solo análisis estático)
- `knowledge_base` (setup inicial: patterns.json, sector_intelligence.json)
- `intelligence_report.md` (primer reporte legible)

**Qué entrega:**
- Primer mapa completo de patrones con n_casos y confianza
- Sector intelligence inicial para todos los sectores con > 3 casos
- Baseline de tasas de conversión por dimensión

**¿Qué riesgo tiene?**
Bajo. Solo lee y organiza. No modifica nada del sistema existente.

**¿Qué impacto comercial tiene?**
Medio. Organiza lo que ya sabemos. No genera inteligencia nueva todavía, pero crea la infraestructura para todo lo que sigue.

**¿Vale la pena construirla?**
Sí. Sin esta fase, todo lo que sigue es ficción.

**Cómo construirla:**
Un script Python (`hint_intelligence/engine.py`) que corre manualmente, lee historial_dataset.json + dataset.json, calcula las mismas tablas que ya calculamos hoy en el análisis ad-hoc, y las persiste en knowledge_base/*.json con confianza y n_casos.

---

### FASE 2 — DETECCIÓN DE CAMBIOS
**"El sistema empieza a notar cuando algo cambia"**

**¿Qué aporta?**
El `change_detector` compara la knowledge_base actual contra la anterior. Cuando algo cambia más allá del umbral, genera una alerta. El usuario no tiene que mirar dashboards para saber si algo está funcionando diferente.

**Módulos de esta fase:**
- `change_detector`
- `alerts.json`
- Visualización de alertas en la UI de index.html (badge rojo con "N alertas")

**Qué entrega:**
- Alertas automáticas de cambios en tasa de dossier por sector
- Alertas de cambios en distribución de objeciones
- Alertas de cambios en rendimiento de variantes

**¿Qué riesgo tiene?**
Medio. Puede generar falsos positivos si el volumen por período es bajo (n < 5 en un período = mucho ruido). Necesita umbrales cuidadosos.

**¿Qué impacto comercial tiene?**
Alto. Hoy los cambios de mercado se descubren semanas después o por accidente. Con este módulo, se detectan en el momento.

**¿Vale la pena construirla?**
Sí. Es el módulo con mejor ratio impacto/esfuerzo después de la Fase 1.

**Cómo construirla:**
El engine corre con un flag `--compare-previous`. Lee la KB actual vs la guardada en la corrida anterior. Calcula delta. Si |delta| > umbral Y n > mínimo → genera alerta.

---

### FASE 3 — RECOMENDACIONES CONTEXTUALES
**"El sistema mejora las decisiones en tiempo real"**

**¿Qué aporta?**
El `recommendation_engine` produce un `context_injection.json` antes de cada generación. El SYSTEM prompt de index.html lo lee y lo incorpora. La IA ahora genera MSG1 sabiendo que "para Energía + Director la variante A convierte 27% vs 19% de la C".

**Módulos de esta fase:**
- `recommendation_engine`
- `context_injection.json`
- Modificación de `generateOpeners()` en index.html para leer e inyectar el contexto

**Qué entrega:**
- Recomendación de variante por sector+seniority
- Recomendación de cliente de referencia por sector
- Señales positivas a buscar en el perfil
- Objeciones probables a preparar

**¿Qué riesgo tiene?**
Medio-alto. Si la KB tiene patrones con confianza baja y el sistema los inyecta como "verdad", puede sesgarse. Necesita mostrar el nivel de confianza junto a la recomendación.

**¿Qué impacto comercial tiene?**
Muy alto. Este es el loop de aprendizaje real. Los datos históricos empiezan a mejorar los mensajes futuros. Si la tasa de dossier aumenta de 25% a 30%, eso son 20 dossiers adicionales cada 400 contactos.

**¿Vale la pena construirla?**
Sí. Es la fase más transformadora de las primeras tres.

**Cómo construirla:**
Cuando el usuario pega un perfil, antes de llamar a la API el frontend hace `GET /api/intelligence?sector=X&seniority=Y`. El servidor lee `context_injection.json` de la KB y devuelve el contexto relevante. Este se agrega como sección adicional al SYSTEM en esa llamada específica.

---

### FASE 4 — EXPERIMENTACIÓN SISTEMÁTICA
**"El sistema diseña sus propios tests"**

**¿Qué aporta?**
El `experiment_engine` detecta las hipótesis que aún no tienen evidencia suficiente y propone tests concretos con n mínimo para conclusión. El usuario puede aceptar o rechazar cada experimento.

**Módulos de esta fase:**
- `experiment_engine`
- `experiments_queue.json`
- UI en index.html: "Tenemos 3 experimentos activos. El EXP_001 ya tiene 12/20 casos."

**Qué entrega:**
- Experimentos propuestos con hipótesis, n mínimo y cómo ejecutar
- Tracking automático de casos que entran a cada experimento
- Conclusiones cuando se alcanza n mínimo

**¿Qué riesgo tiene?**
Bajo. Los experimentos los decide el humano. El engine solo propone y trackea.

**¿Qué impacto comercial tiene?**
Alto a largo plazo. Convierte el outreach de arte a ciencia. Cada duda sobre metodología se convierte en un test medible.

**¿Vale la pena construirla?**
Sí, pero es la última prioridad entre las primeras 4 fases. Solo tiene sentido cuando ya hay suficiente volumen para que los tests sean estadísticamente válidos.

---

### FASE 5 — MEMORIA ESTRATÉGICA
**"El sistema conoce nuestro negocio mejor que nosotros"**

**¿Qué aporta?**
La `knowledge_base` madura. Además de patrones estadísticos, incorpora arquetipos de prospectos: "el Director de Comunicación en Energía que publicó sobre ESG y trabaja en empresa con > 500 empleados tiene 40% de probabilidad de llegar a reunión". El `strategy_engine` produce un brief semanal automatizado.

**Módulos de esta fase:**
- `profile_archetypes.json` (perfiles tipo con sus tasas de conversión)
- `strategy_engine` (síntesis semanal automatizada)
- Integración con el flujo de prospección: "antes de contactar a alguien, el sistema muestra qué arquetipo más se parece y qué tasa histórica tiene"

**Qué entrega:**
- Brief estratégico semanal automatizado
- Arquetipos de prospectos con probabilidad de conversión
- Mapa de oportunidades del mercado

**¿Qué riesgo tiene?**
Medio. Los arquetipos requieren n suficiente por categoría. Si hay pocos casos, los arquetipos son ficción.

**¿Qué impacto comercial tiene?**
Muy alto. Permite priorizar el tiempo de outreach radicalmente mejor. Si el sistema sabe que el arquetipo A convierte al 35% y el B al 8%, el tiempo de Florencia debería ir 80% al arquetipo A.

**¿Vale la pena construirla?**
Sí, cuando se alcancen ~1000 contactos. Con 427 actuales, algunos arquetipos quedarían con n insuficiente.

---

### FASE 6 — INTELIGENCIA PREDICTIVA
**"El sistema predice el futuro"**

**¿Qué aporta?**
El `prediction_engine`. Dado un nuevo perfil (sin haber enviado ningún mensaje todavía), el sistema estima:
- Probabilidad de que responda al MSG1
- Probabilidad de que pida el dossier
- Probabilidad de que llegue a reunión
- Variante y ángulo recomendados con mayor probabilidad de éxito
- Score de prioridad: ¿vale la pena el esfuerzo?

**Cómo funciona:**
Con los patrones de la KB, el knowledge del sector, el seniority y la señal disponible en el perfil, el sistema construye un modelo de scoring basado en los casos históricos similares.

No es machine learning en el sentido técnico. Es scoring por similitud: "de todos los casos en nuestra KB con características parecidas a este perfil, ¿qué porcentaje llegó a dossier? ¿a reunión?"

**Qué entrega:**
- Score de probabilidad por etapa (respuesta, dossier, reunión) para cada prospecto nuevo
- Ranking de prioridad entre múltiples prospectos
- Estimación de effort vs return

**¿Qué riesgo tiene?**
Alto. Los modelos predictivos pueden tener sesgos sistemáticos. Si el sistema siempre predice alta probabilidad para Real Estate porque tiene pocos casos pero buenos resultados, Florencia puede sobreinvertir ahí. El sistema debe mostrar siempre el n_casos que respalda la predicción.

**¿Qué impacto comercial tiene?**
Transformacional. Si el sistema predice correctamente qué prospectos van a llegar a reunión, Florencia puede priorizar su tiempo en los top 20% que generan el 80% de los resultados. Esto es la diferencia entre escalar el outreach y escalar los resultados.

**¿Vale la pena construirla?**
Sí, pero solo en la Fase 6 y solo cuando tengamos > 1500 contactos con resultados medidos. Con 427 casos y solo 2 reuniones confirmadas, el modelo de predicción de "probabilidad de reunión" estaría basado en n=2. Eso no es un modelo. Es ruido.

**Condición de entrada a Fase 6:** > 50 reuniones confirmadas con tracking completo de la trayectoria.

---

## RESUMEN DEL ROADMAP

| Fase | Nombre | Módulos | Impacto | Riesgo | Condición entrada | Priority |
|---|---|---|---|---|---|---|
| 1 | Observación | pattern_engine, knowledge_base | Medio | Bajo | Ahora | 🔴 PRIMERO |
| 2 | Detección de cambios | change_detector, alerts | Alto | Medio | Tras Fase 1 | 🔴 SEGUNDO |
| 3 | Recomendaciones | recommendation_engine, context_injection | Muy Alto | Medio | Tras Fase 2 | 🔴 TERCERO |
| 4 | Experimentación | experiment_engine | Alto (LP) | Bajo | n > 500 contactos | 🟡 CUARTO |
| 5 | Memoria estratégica | profile_archetypes, strategy_engine | Muy Alto | Medio | n > 1000 contactos | 🟡 QUINTO |
| 6 | Predicción | prediction_engine | Transformacional | Alto | n > 50 reuniones confirmadas | 🟢 SEXTO |

---

## ESTRUCTURA DE ARCHIVOS DEL ENGINE

```
hint_intelligence/
├── engine.py              # orquestador principal
├── config.py              # paths, umbrales, constantes
├── pattern_engine.py      # análisis estadístico
├── conversation_engine.py # análisis lingüístico
├── change_detector.py     # detección de cambios
├── recommendation_engine.py
├── experiment_engine.py
├── strategy_engine.py
├── knowledge_base/
│   ├── patterns.json
│   ├── sector_intelligence.json
│   ├── signals.json
│   ├── objection_playbook.json
│   ├── profile_archetypes.json
│   └── experiment_history.json
└── outputs/
    ├── intelligence_report.md
    ├── context_injection.json
    ├── experiments_queue.json
    ├── alerts.json
    └── engine_log.json
```

**Ejecución:**
```
python hint_intelligence/engine.py           # corrida completa
python hint_intelligence/engine.py --phase 1  # solo observación
python hint_intelligence/engine.py --compare  # solo detección de cambios
python hint_intelligence/engine.py --report   # solo genera reporte
```

---

## UNA SOLA PREGUNTA

Antes de construir cualquier parte del HIE, cada módulo debe responder:

> **"¿Esto aumenta la probabilidad de conseguir más reuniones con mejores clientes?"**

**pattern_engine:** Sí. Saber qué sectores y variantes convierten más permite enfocar el esfuerzo.

**change_detector:** Sí. Detectar que Retail cayó a 0% evita desperdiciar tiempo en el sector equivocado.

**recommendation_engine:** Sí. Inyectar contexto histórico en la generación produce mensajes más alineados con lo que históricamente funcionó.

**experiment_engine:** Sí. Resolver las incógnitas metodológicas (¿A vs C realmente?) permite optimizar la estrategia con certeza.

**strategy_engine:** Sí. Un brief semanal automatizado significa que Florencia siempre sabe dónde invertir el tiempo.

**prediction_engine:** Sí (cuando haya suficientes datos). Predecir qué prospectos tienen mayor probabilidad de llegar a reunión es la ventaja competitiva definitiva.

---

*Documento de arquitectura · No contiene código · Está listo para implementar fase por fase · Empezar por Fase 1.*
