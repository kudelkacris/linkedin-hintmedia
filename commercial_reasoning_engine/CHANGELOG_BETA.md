# CHANGELOG_BETA — CRE Historial de Cambios por Evidencia

Este archivo registra cada cambio introducido al CRE durante y después de la Beta.

**Reglas:**
- Cada entrada describe exactamente UN cambio a UN módulo.
- Toda entrada debe incluir: caso que lo originó, categoría del error, módulo raíz, fix aplicado, y resultado en el benchmark.
- No se registran cambios sin evidencia en el dataset.
- Si un cambio no mejora el benchmark, se revierte y se documenta aquí igual.

**Referencia:** `docs/beta_protocol.md` — Secciones 3, 4 y 7.

---

## Beta v1.0 — Benchmark inicial

**Dataset:** `beta_dataset/` (10 conversaciones, congeladas)  
**Versión CRE:** v1.0 (commit 4aadf20)  
**Fecha inicio:** —  
**Fecha cierre:** —

### Resultados

| Caso | Tipo | Categoría | Módulo raíz | Tiempo identificación | Diagnóstico |
|------|------|-----------|-------------|----------------------|-------------|
| 001 | MSG2 LOW | — | — | — | — |
| 002 | MSG2 MEDIUM | — | — | — | — |
| 003 | MSG2 HIGH | — | — | — | — |
| 004 | SEG1 LOW | — | — | — | — |
| 005 | SEG1 MEDIUM | — | — | — | — |
| 006 | SEG1 HIGH | — | — | — | — |
| 007 | SEG2 | — | — | — | — |
| 008 | Recovery | — | — | — | — |
| 009 | Edge | — | — | — | — |
| 010 | Complex | — | — | — | — |

### Resumen

| Métrica | Valor |
|---------|-------|
| PASS | — / 10 |
| EXPECTED FAIL | — / 10 |
| FALSE POSITIVE | — / 10 |
| FALSE NEGATIVE | — / 10 |

**Errores por módulo:**

| Módulo | Errores |
|--------|---------|
| Analyzer | — |
| Evidence | — |
| Classifier | — |
| Strategy | — |
| Context | — |
| LLM | — |
| Reviewer | — |

---

## Correcciones post-Beta v1.0

<!-- Cada corrección sigue este formato:

### Fix #001 — [Fecha]

**Caso origen:** 006  
**Categoría:** FALSE POSITIVE  
**Módulo raíz:** Context Builder  
**Tiempo hasta identificar módulo raíz:** 4 min  
**Problema:** El Reviewer rechazó un draft correcto porque allowed_claims estaba vacío.  
**Fix:** Se agregó X en context_builder/builder.py línea Y.  
**Benchmark después del fix:** 9/10 PASS  

-->