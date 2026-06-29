# Auditoría manual — Reporte previo a revisión humana

Este reporte describe la MUESTRA preparada, no resultados de precisión todavía (eso requiere que un humano complete `manual_review_sample.csv` primero).

## Tamaño de los pools disponibles (corrida actual, limit=20)

| Bucket | Disponibles | Muestreados |
|---|---|---|
| HIGH | 37 | 10 |
| MEDIUM | 15 | 10 |
| LOW | 11 | 10 |

## Campos enriquecidos por categoría

**HIGH**:
- AREA: 17
- SECTOR: 12
- MOTIVO_FRACASO: 5
- TIPO_PERFIL: 3

**MEDIUM**:
- TIPO_PERFIL: 11
- MOTIVO_FRACASO: 2
- AREA: 1
- SECTOR: 1

**LOW (suggested)**:
- MOTIVO_FRACASO: 4
- TIPO_PERFIL: 3
- AREA: 2
- SECTOR: 2

## Estimación de riesgo (cualitativa, antes de revisión humana)

- **HIGH**: riesgo bajo esperado — el guardrail de `confidence_engine.py` exige evidencia no vacía y valor dentro del enum para llegar a HIGH. Riesgo residual: alucinación semánticamente plausible que cita evidencia real pero la interpreta mal.
- **MEDIUM**: riesgo medio — mismo guardrail estructural, pero el modelo ya se autoevalúa con menos certeza. Es el bucket donde más vale la pena gastar atención humana.
- **LOW**: no se aplica al dataset (va a `suggested_values.csv`), así que el riesgo de contaminación es nulo — pero vale auditar si el modelo descarta correctamente (falsos negativos: campos que sí tenían evidencia suficiente y quedaron en LOW por error de criterio).

## Metodología propuesta para calcular PRECISION REAL

Después de que un humano complete `CORRECTO` (SI/NO) en `manual_review_sample.csv` para las 30 filas, correr `compute_precision.py`, que calcula:

- `PRECISION_HIGH` = correctos en HIGH / total revisado en HIGH
- `PRECISION_MEDIUM` = correctos en MEDIUM / total revisado en MEDIUM
- `PRECISION_LOW` = correctos en LOW / total revisado en LOW (interpretado como "el modelo descartó bien" cuando CORRECTO=SI sobre un LOW significa que el valor sugerido, aunque no aplicado, era razonable)
- `PRECISION_APPLIED` = correctos en (HIGH ∪ MEDIUM) / total revisado en (HIGH ∪ MEDIUM) — **esta es la métrica que importa para decidir si escalar**, porque HIGH y MEDIUM son los únicos que tocan el dataset real.

**Regla de decisión**: si `PRECISION_APPLIED >= 85%`, el script imprime y deja constancia de `RUN_FULL_BATCH = TRUE` (recomendación, no ejecuta nada solo). Si no llega a 85%, imprime `RUN_FULL_BATCH = FALSE` y debería ajustarse el prompt/guardrails antes de reintentar, no correr el batch completo igual.
