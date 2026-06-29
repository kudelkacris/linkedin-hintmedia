# AI Enrichment Pipeline — V1

Completa SOLO los campos vacíos del dataset generado por `dataset_builder/` (que usa regex/heurísticas
sin IA). Esta etapa sí usa IA — pero con guardrails duros para no inventar.

## Uso

```
cd ai_enrichment
python enrichment_pipeline.py --limit 20   # modo prueba, default
python enrichment_pipeline.py --limit 0    # corre sobre los 137 candidatos completos de needs_ai_review.csv
```

Requiere `ANTHROPIC_API_KEY` en `../.env.local` (mismo archivo que usa `servidor.py`).

## Input

- `dataset_builder/outputs/needs_ai_review.csv` — lista de conversaciones candidatas (137 de 167)
- `dataset_builder/outputs/dataset.json` — registro completo de cada conversación (para ver qué campos están realmente vacíos)
- `conversaciones/*.md` — texto original completo (perfil + conversación real), única fuente de evidencia permitida

## Arquitectura

- `config.py` — rutas, campos objetivo (`TARGET_FIELDS`), enums válidos por campo (`VALID_VALUES`)
- `enrichment_prompts.py` — system prompt con la regla "nunca inventar" + builder del prompt por fila, que solo pide los campos vacíos de esa conversación puntual y le pasa al modelo el enum exacto cuando corresponde
- `confidence_engine.py` — guardrails estructurales: si no hay valor, confidence se fuerza a LOW; si hay valor pero sin evidencia citada, downgrade un escalón; si el valor no pertenece al enum del campo, se descarta entero
- `enrichment_validator.py` — decide ruteo: HIGH/MEDIUM con valor → `enriched_dataset.csv`. LOW o vacío → `suggested_values.csv`, nunca al dataset
- `enrichment_pipeline.py` — orquestador: 1 llamada a Claude (haiku-4-5) por conversación, parseo, validación, outputs, stats, report

## 3 bugs reales encontrados y corregidos durante el testing (no hipotéticos)

1. **MOTIVO_EXITO/MOTIVO_FRACASO pedidos sin filtrar por RESULTADO_FINAL.** Para una conversación con resultado `DOSSIER` (ni éxito ni fracaso definitivo), el pipeline le pedía a la IA ambos motivos igual, y la IA — sin objetar — completaba los dos con evidencia real pero fuera de contexto semántico (ej. "cambio de rol" como motivo de fracaso en una conversación que en realidad seguía abierta). Corregido: `fields_missing()` ahora respeta la misma regla que `dataset_builder/heuristics.py` (motivo_exito solo si CLIENTE/REUNION, motivo_fracaso solo si SIN_RESPUESTA).
2. **Regex de parseo usaba `\s*` entre `:` y el valor.** `\s` matchea también `\n`. Cuando un campo quedaba vacío (ej. `AREA:` sin nada después), el regex se comía el salto de línea y capturaba la línea siguiente completa, corriendo todos los valores un campo hacia adelante (`AREA` terminaba con el valor de `AREA_CONFIDENCE`, etc.). Corregido a `[ \t]*` (solo espacio/tab, nunca salto de línea).
3. **Enums no se le pasaban al modelo.** Para campos con categorías fijas (TIPO_PERFIL, NIVEL_SENIORITY, ENGAGEMENT_LEVEL, OBJECION_PRINCIPAL) el prompt solo describía la regla en general, sin listar las opciones exactas — el modelo respondía en prosa libre ("Tomador de Decisión") que el guardrail de enum correctamente descartaba, pero perdía cobertura evitable. Corregido: el prompt ahora lista el enum exacto por campo. Resultado en la prueba de 20: aplicados subió de 37 a 52, LOW bajó de 26 a 11.

## Resultado de la prueba con 20 registros reales (última corrida, post-fixes)

- Procesados: 20/20, 0 errores
- Campos aplicados (HIGH/MEDIUM, van a `enriched_dataset.csv`): 52
- Campos solo sugeridos (LOW, van a `suggested_values.csv`, NO tocan el dataset): 11
- Distribución de confianza: HIGH 37, MEDIUM 15, LOW 11
- Ver ejemplos reales con evidencia citada en `outputs/enriched_dataset.csv`

## Precisión estimada

No se midió contra ground truth manual (no existe ground truth etiquetado a mano para comparar). La
precisión real depende de qué tan bien el modelo respeta "no inventar" — los guardrails estructurales
(`confidence_engine.py`) capturan las violaciones detectables por código (enum inválido, valor sin
evidencia, valor vacío con confidence alta) pero NO pueden detectar una alucinación semántica
plausible (ej. inferir un sector incorrecto pero coherente con el cargo). Recomendación antes de usar
`enriched_dataset.csv` para ajustar reglas de negocio: revisar manualmente una muestra de 15-20 filas
HIGH y confirmar que la evidencia citada realmente sostiene el valor.

## Por qué `suggested_values.csv` existe y no se descarta directamente

Cada fila ahí tiene `GUARDRAIL_NOTES` explicando por qué no se aplicó (enum inválido, sin evidencia,
etc.) — sirve para detectar patrones de fields que el modelo nunca puede resolver con la evidencia
disponible (ej. SECTOR cuando ni el cargo ni la empresa lo insinúan), información útil para decidir si
vale la pena pedir ese dato a mano en el futuro en vez de inferirlo.

## Trazabilidad

Cada valor en `enriched_dataset.csv` tiene su `EVIDENCE` (cita textual concreta) y `REASON` (máx. 50
palabras) en la misma fila — se puede auditar cualquier valor sin volver a correr el pipeline.

## Correr sobre los 137 registros completos

`python enrichment_pipeline.py --limit 0`. No se corrió en V1 por costo/tiempo de API — se entregó
deliberadamente solo la prueba de 20 pedida. Antes de correr el batch completo, conviene revisar a
mano la muestra de 20 ya generada para confirmar que el criterio de calidad es aceptable.
