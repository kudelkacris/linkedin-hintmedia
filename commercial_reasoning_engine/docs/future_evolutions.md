# Future Evolutions — Commercial Reasoning Engine

Documented decisions NOT yet implemented. Each item requires explicit approval before starting.

---

## EVOLUCIÓN 1 — rotation_engine: enum-based MSG2_ANGLE

**Estado:** pendiente. No modificar código hasta aprobación.

**Problema actual:**
`rotation_engine.py` trabaja con strings libres para `previous_msg2_angle`.
El matching usa exact → substring → default, lo que es frágil ante variaciones de texto.

**Solución propuesta:**
El analyzer deberá producir un enum tipado `MSG2Angle` en lugar de un string.

```python
class MSG2Angle(str, Enum):
    COMMUNICATION  = "comunicacion"      # narrativa, comunicación, vocería
    BRANDING       = "branding"          # identidad, branding, marca
    CONTENT        = "contenido"         # contenido, alcance, redes
    PAID_MEDIA     = "paid_media"        # campañas, paid, meta, google
    WORKLOAD       = "workload"          # carga operativa, equipo, recursos
    POSITIONING    = "posicionamiento"   # posicionamiento personal, CEO branding
    UNKNOWN        = "unknown"
```

`rotation_engine.py` usará `MSG2Angle` en lugar de strings.
El `rotation_map.json` tendrá keys = valores del enum.

**Impacto de módulos:**
- `schemas/analysis.py` — `previous_msg2_angle: Optional[MSG2Angle]`
- `analyzer/analyzer.py` — detectar y clasificar el ángulo del MSG2 anterior
- `strategy/rotation_engine.py` — reescribir lógica con enum
- `config/rotation_map.json` — ajustar keys a valores del enum

---

## EVOLUCIÓN 2 — strategy_builder: decisiones abstractas en lugar de flags de lenguaje

**Estado:** pendiente. No modificar código hasta aprobación.

**Problema actual:**
`strategy_builder.py` produce campos como `mention_hint: bool` y `mention_dossier: bool`
que describen instrucciones de lenguaje, no decisiones comerciales puras.
Esto mezcla la capa de decisión con la capa de redacción.

**Solución propuesta:**
Reemplazar flags de lenguaje por decisiones abstractas:

```python
# En schemas/strategy.py — StrategyDecision

# Actual (mezcla lenguaje + decisión):
mention_hint: bool
mention_dossier: bool

# Propuesto (decisión pura):
need_hint_reference: bool      # el motor decidió que Hint debe aparecer
need_client_example: bool      # el motor decidió que un cliente debe aparecer
need_dossier_reference: bool   # el motor decidió que el dossier debe aparecer
```

**Responsabilidad del Context Builder:**
El `context_builder/builder.py` traduce esas decisiones abstractas
a instrucciones concretas para el LLM en `allowed_topics` y `forbidden_topics`.
El strategy_builder no sabe cómo se traducen. Solo decide.

**Impacto de módulos:**
- `schemas/strategy.py` — reemplazar los tres campos
- `strategy/strategy_builder.py` — actualizar nombres
- `context_builder/builder.py` — actualizar `_build_allowed_topics` y `_build_forbidden_topics`
- `tests/test_hito5.py` — actualizar assertions
- `tests/test_hito6.py` — actualizar assertions

---

*Versión: 1.0 — Documentadas 2026-07-08. Derivadas de aprobación HITO 5.*
