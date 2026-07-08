# ARCHITECTURE LOCK — Commercial Reasoning Engine
**Versión:** v2.0
**Estado:** CONGELADA
**Fecha de aprobación:** 2026-07-08

---

## PRINCIPIO FUNDAMENTAL

El LLM deja de tomar decisiones.
El motor toma las decisiones.
El LLM solo redacta.

Todo el razonamiento comercial ocurre fuera del LLM.
El LLM recibe un JSON estructurado y convierte decisiones en lenguaje natural.
Nada más.

---

## PIPELINE OFICIAL

```
run.py
  │
  ├─ dataset/reader.py          lee .md del prospecto (solo lectura)
  ├─ analyzer/parser.py         texto crudo → ConversationInput
  ├─ analyzer/analyzer.py       ConversationInput → AnalysisResult
  ├─ evidence_engine/engine.py  AnalysisResult → EvidenceInventory
  │   [ÚNICO PUNTO DE BLOQUEO: si no hay evidencia REAL usable → STOP]
  ├─ classifier/action_classifier.py   → ActionClassification
  ├─ classifier/strategy_classifier.py → StrategyClassification
  ├─ strategy/strategy_builder.py      → StrategyDecision
  │   [BLOQUEO: si strategy.blocked == True → STOP]
  ├─ context_builder/builder.py        → LLMContext
  ├─ llm/adapter.py                    → mensaje_draft (string)
  ├─ reviewer/reviewer.py              → ReviewResult
  │   [BLOQUEO: si review.approved == False → log + STOP]
  └─ decision_log/trace.py             guarda DecisionTrace completo
```

---

## ÁRBOL DE MÓDULOS OFICIAL

```
commercial_reasoning_engine/
│
├── schemas/              contratos de datos entre módulos
│   ├── conversation.py   ConversationInput, Message
│   ├── analysis.py       AnalysisResult
│   ├── evidence.py       Evidence, EvidenceInventory
│   ├── classification.py ActionClassification, StrategyClassification
│   ├── strategy.py       StrategyDecision, Bubble, CTADecision
│   ├── context.py        LLMContext, FormatRules
│   ├── review.py         ReviewResult, ReviewViolation
│   └── decision_log.py   DecisionLogStep, DecisionTrace
│
├── config/               conocimiento comercial como datos, nunca como código
│   ├── blocklist.json    frases prohibidas exactas
│   ├── sectors.json      sector → clientes Hint + stats HIE
│   ├── seniority.json    seniority → estrategia + justificación reunión
│   ├── rotation_map.json ángulo MSG2 → ángulo SEG1 obligatorio
│   ├── win_personal.json rol → wins personales frecuentes
│   └── playbook.json     reglas del protocolo como datos
│
├── analyzer/
│   ├── parser.py         texto crudo → ConversationInput
│   └── analyzer.py       ConversationInput → AnalysisResult
│
├── evidence_engine/
│   ├── engine.py         produce EvidenceInventory
│   ├── tagger.py         etiqueta cada claim REAL/INFERRED/UNKNOWN
│   └── validator.py      marca usable=False si INFERRED o UNKNOWN
│
├── classifier/
│   ├── action_classifier.py    → MSG2/SEG1/SEG2/WAIT/NONE
│   └── strategy_classifier.py → CONSULTIVA/ENTRE_PARES/EXPLORATORIA
│
├── strategy/
│   ├── strategy_builder.py  consolida todas las decisiones comerciales
│   ├── rotation_engine.py   calcula rotación de ángulo MSG2→SEG1
│   └── win_selector.py      elige win personal según evidencia REAL
│
├── context_builder/
│   └── builder.py       StrategyDecision → LLMContext (allowed/forbidden topics)
│
├── llm/
│   ├── adapter.py        interfaz abstracta LLM-agnostic
│   ├── claude_adapter.py implementación Claude
│   └── prompts/
│       ├── msg2.txt
│       ├── seg1.txt
│       └── seg2.txt
│
├── reviewer/
│   ├── reviewer.py           orquesta todos los checks
│   ├── blocklist_checker.py  verifica frases prohibidas
│   ├── perspective_checker.py verifica primer sujeto del mensaje
│   └── evidence_checker.py   verifica que INFERRED no filtró al draft
│
├── decision_log/
│   ├── logger.py   cada módulo llama log(module, output, duration_ms)
│   └── trace.py    ensambla DecisionTrace al final de cada corrida
│
├── dataset/
│   └── reader.py   lee .md del prospecto (solo lectura, nunca escribe)
│
├── logs/
│   └── decisions/  un JSON por corrida: {run_id}_{prospect}.json
│
├── docs/
│   ├── architecture.md     (apunta a este archivo)
│   ├── schema_reference.md
│   └── hitos.md
│
└── run.py          entry point
```

---

## RESPONSABILIDAD DE CADA MÓDULO

| Módulo | Responsabilidad única | Prohibido |
|---|---|---|
| `parser` | Convertir texto crudo en estructura | Interpretar contenido |
| `analyzer` | Extraer hechos observables | Inferir, interpretar, decidir |
| `evidence_engine` | Etiquetar cada afirmación REAL/INFERRED/UNKNOWN | Inventar, rellenar huecos |
| `action_classifier` | Decidir qué mensaje enviar | Decidir cómo o con qué tono |
| `strategy_classifier` | Decidir el tipo de relación | Decidir el contenido |
| `strategy_builder` | Tomar todas las decisiones comerciales | Redactar texto |
| `rotation_engine` | Calcular rotación de ángulo | Evaluar si el ángulo es bueno |
| `win_selector` | Elegir el win personal | Evaluar si es relevante para el mensaje |
| `context_builder` | Reducir decisiones a JSON mínimo | Agregar información no decidida |
| `llm/adapter` | Convertir JSON en texto natural | Decidir cualquier cosa |
| `reviewer` | Aprobar o rechazar el draft | Corregir o reescribir |
| `decision_log` | Registrar outputs de cada módulo | Modificar outputs |
| `dataset/reader` | Leer .md del prospecto | Escribir, modificar, crear archivos |

---

## REGLA DE UNA RESPONSABILIDAD

Un módulo que clasifica NO interpreta estrategia.
Un módulo que analiza NO decide acciones.
Un módulo que construye contexto NO redacta texto.
Un módulo que redacta NO decide nada.

Si durante la implementación un módulo necesita hacer algo que pertenece a otro módulo,
la solución es pasar el output del otro módulo como input, nunca duplicar la lógica.

---

## COMUNICACIÓN ENTRE MÓDULOS

**Regla absoluta:** todo inter-módulo via schema tipado. Nunca strings libres.

```
parser      → ConversationInput
analyzer    → AnalysisResult
evidence    → EvidenceInventory
classifier  → ActionClassification, StrategyClassification
strategy    → StrategyDecision
context     → LLMContext
llm         → str (draft, único caso de string — output final del LLM)
reviewer    → ReviewResult
```

Cada schema está definido en `schemas/`. Ningún módulo define sus propios tipos.

---

## REGLA FUNDAMENTAL DEL EVIDENCE ENGINE

Si `EvidenceInventory.evidence_real` está vacío → `blocked = True`.
El sistema se detiene. Devuelve `block_reason`.
Nunca rellena con información inferida o del sector.

Esta regla no tiene excepciones.

---

## REGLA DEL CONTEXT BUILDER

El LLM nunca recibe:
- La conversación completa
- El archivo .md del prospecto
- El CLAUDE.md
- Más de lo que está en LLMContext

El LLM recibe exactamente `LLMContext`, que incluye:
- `allowed_topics`: lista de temas que puede mencionar
- `forbidden_topics`: lista de temas que no puede mencionar
- `allowed_claims`: citas exactas del prospecto que puede usar
- `forbidden_claims`: información inferida que no puede aparecer

---

## REGLA DE INTERCAMBIABILIDAD DE LLM

`llm/adapter.py` es una interfaz abstracta.
`llm/claude_adapter.py` es una implementación.

Si mañana se cambia Claude por GPT o Gemini:
- Se crea `llm/gpt_adapter.py`
- Se cambia el adapter en `run.py`
- Cero cambios en el resto del sistema

El conocimiento comercial vive en el motor, nunca en el modelo.

---

## ROADMAP DE HITOS

| Hito | Módulos | Dependencias |
|---|---|---|
| 1 | schemas/ + config/ | ninguna |
| 2 | analyzer/parser + analyzer/analyzer + dataset/reader | Hito 1 |
| 3 | evidence_engine/ | Hito 1, 2 |
| 4 | classifier/ | Hito 1, 2 |
| 5 | strategy/ | Hito 1, 2, 3, 4 |
| 6 | context_builder/ | Hito 5 |
| 7 | llm/ | Hito 6 |
| 8 | reviewer/ | Hito 6, 7 |
| 9 | decision_log/ + run.py + integración end-to-end | todos |

Cada hito se inicia solo con aprobación explícita del anterior.

---

## REGLA DE VERSIONADO

Esta arquitectura es v2.0.
Está CONGELADA.

Cualquier cambio estructural futuro requiere:
1. Propuesta escrita con justificación
2. Aprobación explícita
3. Nuevo número de versión (v2.1, v2.2, v3.0)
4. Nuevo archivo ARCHITECTURE_LOCK_v{version}.md

Esta versión (v2.0) nunca se modifica una vez aprobada.
Los cambios van en archivos nuevos, nunca en este.

---

*Arquitectura aprobada: 2026-07-08. Construida para sobrevivir cambios de LLM.*
