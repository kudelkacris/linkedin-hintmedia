# Commercial Reasoning Engine (CRE)

> El objetivo del CRE no es evitar errores. Es hacer que cada error sea localizable, explicable y corregible sin afectar el resto del sistema.

---

| | |
|-|-|
| **Versión** | v1.0 |
| **Estado** | Stable |
| **Tests** | 317 |
| **Arquitectura** | Congelada |
| **Motor** | Determinístico |
| **LLM** | Claude (swappable) |
| **Última Beta** | Pendiente |

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

| Documento | Pregunta que responde |
|-----------|----------------------|
| `README.md` | ¿Qué es el CRE? |
| `ARCHITECTURE_LOCK.md` | ¿Cómo está construido? |
| `docs/ENGINE_PHILOSOPHY.md` | ¿Para qué existe? ¿Qué principios lo gobiernan? |
| `docs/DESIGN_DECISIONS.md` | ¿Por qué cada decisión es como es? |
| `docs/beta_protocol.md` | ¿Cómo sabemos si funciona bien? |
| `CHANGELOG_BETA.md` | ¿Cómo fue mejorando? |

## KPIs

| KPI | Target | Qué mide |
|-----|--------|----------|
| Tiempo hasta módulo raíz | < 10 min | Observabilidad del sistema |
| Precisión del módulo raíz | 100% | Calidad del diagnóstico |
| Impacto del fix | +n/10 | El motor está aprendiendo |
| Distancia del fix | 1 módulo | Integridad de la arquitectura |

## Tests

317 tests — HITO 1 al 9.

```
pytest commercial_reasoning_engine/tests/
```

## Roadmap

| Versión | Foco |
|---------|------|
| **v1.0** | Pipeline completo, arquitectura congelada ← *actual* |
| **v1.1** | Mejoras al Analyzer y Strategy Builder basadas en Beta |
| **v1.2** | Mejores prompts y rotación de ángulos |
| **v2.0** | Multi-idioma (español / inglés) |
| **v3.0** | Razonamiento probabilístico sobre historial de conversiones |

## Versión

CRE v1.0 — commit `4aadf20` — tag `cre-v1.0`  
Rama estable: `cre-v1.0-stable`
