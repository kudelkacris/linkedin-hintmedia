# Commercial Reasoning Engine (CRE)

> El objetivo del CRE no es evitar errores. Es hacer que cada error sea localizable, explicable y corregible sin afectar el resto del sistema.

---

## Qué es

Motor de razonamiento comercial para outreach de LinkedIn (Hint Media).

Todas las decisiones comerciales ocurren antes del LLM. El LLM solo redacta.

```
ConversationInput
    → Analyzer          analizar stage, engagement, sector, seniority
    → Evidence Engine   clasificar evidencia real vs inferida
    → Classifier        elegir acción (MSG2 / SEG1 / SEG2 / WAIT)
    → Strategy Builder  construir una decisión comercial única
    → Context Builder   armar el contexto mínimo para el LLM
    → LLM Adapter       redactar el mensaje
    → Reviewer          auditar blocklist, perspectiva, evidencia
    → RunResult
```

## Uso

```python
from commercial_reasoning_engine.run import run
from commercial_reasoning_engine.llm.claude_adapter import ClaudeAdapter
from commercial_reasoning_engine.schemas.conversation import ConversationInput

result = run(conversation, adapter=ClaudeAdapter(), debug=True, log_dir=Path("decision_logs"))
if result.approved:
    print(result.final_message)
```

## Documentos constitucionales

| Documento | Rol |
|-----------|-----|
| `ARCHITECTURE_LOCK.md` | Cómo está construido el CRE |
| `docs/beta_protocol.md` | Cómo se valida el CRE |
| `CHANGELOG_BETA.md` | Qué cambió, por qué, con qué evidencia |

## KPIs

| KPI | Target | Qué mide |
|-----|--------|----------|
| Tiempo hasta módulo raíz | < 10 min | Observabilidad del sistema |
| Precisión del módulo raíz | 100% | Calidad del diagnóstico |
| Impacto del fix | +n/10 | El motor está aprendiendo |
| Distancia del fix | 1 módulo | Integridad de la arquitectura |

Si la distancia del fix sube consistentemente por encima de 1, el diseño está degradándose.

## Tests

317 tests — HITO 1 al 9.

```
pytest commercial_reasoning_engine/tests/
```

## Versión

CRE v1.0 — commit `4aadf20` — tag `cre-v1.0`  
Rama estable: `cre-v1.0-stable`
