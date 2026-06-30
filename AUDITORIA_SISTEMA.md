# Auditoría del sistema — Generador LinkedIn Hint Media

Fecha: 2026-06-29. Alcance: index.html (2068 líneas), servidor.py (161 líneas), historial.json.

## 1. Arquitectura actual

```
Browser (index.html, todo el JS embebido)
   │  fetch /api/generate { prompt, system }
   ▼
servidor.py (http.server puro, sin framework)
   │  proxy a Anthropic API (system con cache_control ephemeral)
   ▼
Claude (haiku-4-5) → responde texto plano con formato fijo
   │
   ▼
Browser parsea con regex → renderiza burbujas → guarda en historial.json
```

No hay base de datos, no hay backend de negocio: servidor.py es un proxy + persistencia de archivo plano. Toda la lógica (prompts, parsing, UI, scoring, historial) vive en index.html.

## 2. Flujo de datos (3 entry points a la API)

1. **generateOpeners()** (línea 826): perfil pegado → prompt con formato completo (RESUMEN, HECHOS, ..., ---VARIANTE---×2, ---MSG3/4/SEG1/2---). Usa `SYSTEM` (línea 396) como system prompt cacheado.
2. **handleReply()** (línea 1165): conversación acumulada + nueva respuesta del prospecto → prompt distinto, formato `BURBUJA\d+:` + `ENGAGEMENT_LEVEL` + `ANALISIS` + `SIGUIENTE`. Mismo `SYSTEM`.
3. **callAPI()** (línea 1278): wrapper único, llama a `/api/generate`.

Cada uno tiene su propio formato de salida y su propio parser. No comparten función de parsing.

## 3. Parsers existentes (todos basados en regex sobre texto plano)

- `getField(key)` (línea 934): `^KEY:\s*(.+)` por línea, multilinea con flag `m`. Usado para RESUMEN, HECHOS, INTERPRETACION_TRABAJO, SEÑAL_HUMANA, TENSION_PROFESIONAL, HIPOTESIS_CONVERSACIONAL, ANGULO, INFERENCE_RISK, IRREPETIBILIDAD, DEBILIDADES_DE_ESTA_SECUENCIA, CONFIDENCE_SCORE.
- `parseFixedBlock(tag)` (línea 979): extrae bloque entre `---TAG---` y el siguiente `---`, lee líneas `B\d+:`. Usado para MSG3, MSG4, SEG1, SEG2.
- Parsing de `---VARIANTE---` (línea 992): split por separador, cada bloque parseado línea por línea buscando `TITULO:`, `SCORE:`, `TIP:`, `MSG1_B\d+:`, `MSG2_B\d+:`, `RESPUESTA:`.
- En `handleReply`: parseo manual de `BURBUJA\d+:`, `ANALISIS:`, `SIGUIENTE:`, `ENGAGEMENT_LEVEL:` (línea 1226).

**Punto clave para Fase 2-7**: `getField()` es independiente por clave — agregar una clave nueva al texto de salida (ej. `CONFIDENCE_LEVEL:`) NO rompe el parsing de las claves existentes, siempre que:
- la clave nueva no colisione con un nombre ya usado,
- se agregue su propio `getField('NUEVA_CLAVE')` en el JS,
- no se inserte en medio de un bloque que otro regex delimita por posición (ej. dentro de `---VARIANTE---`).

Esto hace que las Fases 2 (Confidence), 3 (Clasificación), 4 (Scoring) sean de **bajo riesgo estructural**: son campos de auditoría adicionales en la sección de análisis estratégico, mismo patrón que `INFERENCE_RISK`/`CONFIDENCE_SCORE` que ya existen y conviven sin problema.

## 4. Dependencias y acoplamientos críticos

- **SYSTEM** es un solo string gigante (line 396-806). Cualquier cambio se cachea con `cache_control: ephemeral` — cambiar el contenido invalida el cache (no rompe nada, solo cuesta el primer request más).
- **El prompt de generateOpeners() repite el formato de salida** (líneas 850-902) que YA está descrito dentro de SYSTEM (líneas 745-806). Está duplicado — si se agrega un campo, hay que tocar dos lugares: el SYSTEM (regla general) y el prompt template del request (el formato exacto exigido). Mismo patrón en handleReply (no duplica formato completo, es más corto).
- **historial.json**: estructura por entrada es libre (no hay schema validation). Campos usados: `id, date, name, empresa, variantTitle, profileRaw, msg1, msg2, extraMsgs, conversationHistory, stage, stageHistory, noInterest, dossierMail, tipoPerfil, sector, nivelInteres, senalDetectada, anguloMsg1, hipotesisMsg2, estadoActual`. Los últimos 7 campos (`tipoPerfil`...`estadoActual`) ya existen como **inputs manuales editables** (línea 1424 `structFieldHtml`) — NO se llenan automáticamente con IA todavía. Esto es relevante para Fase 3/6/7: ya hay un lugar pensado para guardar clasificación, pero hoy es manual.
- **Render de variantes** (`renderVariants`, línea 917) asume exactamente hasta 4 bloques `---VARIANTE---` (línea 997: `.slice(startIdx, startIdx+4)`) y arrays fijos `tagClass`/`tagLabel` de 4 elementos. Agregar variantes nuevas SÍ rompe esto. Agregar *campos* dentro de los bloques existentes NO rompe esto (cada variante ya tiene `get(k)` genérico, línea 1004).
- **UI**: todo vive en un solo `<script>` sin módulos. Variables globales (`state`, `_histEntries`, `_histStageFilter`). Agregar paneles nuevos es seguro si son funciones nuevas + un contenedor DOM nuevo, sin tocar las funciones existentes.

## 5. Riesgos de romper retrocompatibilidad por fase

| Fase | Riesgo | Por qué |
|---|---|---|
| 2 — Confidence | Bajo | Mismo patrón que campos de auditoría ya existentes (no afecta mensajes, solo display) |
| 3 — Clasificación perfil | Bajo | Campos nuevos de solo lectura, no tocan parser de variantes |
| 4 — Scoring | Bajo | Igual que 2/3 |
| 5 — Objeciones | Medio | Si influye automáticamente en SEG1/SEG2 (como pide el usuario), hay que tocar el prompt de `handleReply()` y su lógica condicional — ahí sí se interactúa con generación real, no solo con display |
| 6 — Tracking interno | Bajo-medio | Los campos para esto ya existen en historial.json (manuales). Pasar a automático requiere que el modelo los devuelva y un parser nuevo los guarde — aditivo, no reemplaza nada si se mantienen los campos manuales como fallback |
| 7 — Memoria por empresa | Bajo | Solo lectura sobre `_histEntries` filtrando por `empresa`, sin tocar generación |
| 8 — UX paneles | Bajo | Aditivo en el DOM, no toca generación/parsers actuales |
| 9 — Backup/rollback | N/A | Proceso, no código |

**Riesgo transversal más importante**: el prompt-template de `generateOpeners()` (líneas 844-902) duplica el formato del SYSTEM. Cualquier fase que agregue salida al modelo debe actualizar **ambos** lugares o el modelo no sabrá que debe emitir el campo nuevo en ese flujo específico. `handleReply()` tiene su propio prompt corto (línea 1188) — si Fase 5/6 necesitan que el modelo devuelva más campos ahí, hay que tocarlo aparte.

## 6. Propuesta de implementación (orden recomendado)

1. **Fase 2 (Confidence) + Fase 3 (Clasificación) + Fase 4 (Scoring)** juntas, en un solo paso: son aditivas, mismo patrón, bajo riesgo. Se agregan como nuevas secciones de salida en el bloque de análisis estratégico (no en las variantes), con sus propios `getField()` y un bloque de display nuevo (acordeón colapsable, Fase 8 parcial).
2. **Fase 7 (Memoria por empresa)**: solo lectura sobre datos que ya existen en historial.json, sin downstream a IA. Implementable independiente de las anteriores.
3. **Fase 6 (Tracking)**: aprovechar campos ya existentes (`tipoPerfil`, `sector`, etc.) y agregar los que falten (`CURRENT_STAGE` ya existe como `stage`, agregar `PROBABILITY_CLOSE`, `NEXT_ACTION`, `FOLLOWUP_RECOMMENDED_DAYS`). Decidir si el modelo los autocompleta o se mantienen editables a mano (recomendado: autocompletar pero dejar editable, igual que hoy).
4. **Fase 5 (Objeciones)**: la única que toca lógica de generación real (afecta SEG1/SEG2). Requiere tocar el prompt de `handleReply()`, no solo el display. Hacerla al final, después de validar que las fases aditivas no rompieron nada.
5. **Fase 8 (UX)**: en paralelo a cada fase, no como paso separado al final — cada fase agrega su propio acordeón.
6. **Fase 9 (Seguridad)**: git commit antes de cada fase (ya es un repo git), no requiere tooling nuevo.

## 7. Qué NO se modifica (garantía de retrocompatibilidad)

- Formato `---VARIANTE---`, `MSG1_B\d+`, `MSG2_B\d+`, `---MSG3/4/SEG1/2---`, `B\d+:` — intactos.
- Reglas de tono, CTA, blocklist de frases, clientes por sector — intactos.
- `historial.json` — solo se agregan campos, ninguno se renombra ni se elimina.
- UI existente (cards, botones, flujo de generación) — intacta, solo se agregan paneles nuevos.
