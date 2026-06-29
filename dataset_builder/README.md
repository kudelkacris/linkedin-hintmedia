# Hint Intelligence Dataset Builder — V1

Convierte `conversaciones/*.md` (fuente de verdad) + `historial.json` (fallback) en un dataset
estructurado de conversaciones reales, sin usar IA para la extracción inicial.

## Uso

```
cd dataset_builder
python dataset_builder.py
```

Lee todos los `.md` en `../conversaciones/`, parsea, clasifica por regex/heurísticas, y escribe en `outputs/`:

- `dataset.csv` / `dataset.json` — los 167 registros con los 26 campos del esquema + `NEEDS_AI`
- `needs_ai_review.csv` — solo los registros con huecos en campos críticos (objeción, engagement, tipo de perfil, motivo de éxito/fracaso)
- `stats.json` — métricas y distribuciones en formato máquina
- `report.md` — el mismo análisis en tablas legibles

## Arquitectura

- `config.py` — rutas, lista de campos del esquema, diccionarios de keywords (objeción, CTA de llamada, cliente cerrado, seniority, tipo de perfil)
- `extractors.py` — parsers puros de texto: detecta formato (markdown plano vs frontmatter), extrae campos en negrita (`**Campo:** valor`), separa secciones `## ...` en bloques (MSG1, MSG2, respuestas, SEG1/2, dossier, notas). No clasifica nada, solo estructura el texto crudo.
- `heuristics.py` — toma el dict crudo de `extractors` y aplica reglas (regex/keywords) para llenar los 26 campos del esquema. Cuando una regla no puede decidir, el campo queda vacío.
- `analytics.py` — tasas globales, distribuciones por sector/país/cargo/engagement/objeción, conversión por segmento, y el render de `report.md`.
- `dataset_builder.py` — orquestador: itera los `.md`, llama extractors→heuristics, completa huecos desde `historial.json` por nombre, escribe los 5 outputs y loggea en consola.

## Decisión de diseño importante: de dónde se toma cada señal

`CALL_AGENDADA`, `CLIENTE_CERRADO` y `OBJECION_PRINCIPAL` se calculan **solo** sobre las respuestas
reales del prospecto + `Estado` + `Notas` — nunca sobre el texto completo del archivo. Esto es así
porque nuestros propios mensajes (MSG2, SEG1, SEG2, dossier) siempre proponen una llamada
("coordinamos 15 minutos") como parte del guion, sea o no aceptada. Buscar esas keywords en el
texto completo genera falsos positivos masivos (detectado y corregido en V1: REUNION pasó de 49 a 6
registros tras la corrección).

## Por qué tantos registros quedan en `needs_ai_review.csv` (137/167, 82%)

No es un bug del extractor: la mayoría de los archivos no tiene `Sector` (68%) ni suficiente
información de cargo para inferir `TIPO_PERFIL` (61%) por regex. `MOTIVO_EXITO`/`MOTIVO_FRACASO`
casi siempre quedan vacíos porque son texto libre que requiere comprensión, no patrón. Esto es
exactamente lo que el mecanismo de `NEEDS_AI` está pensado para señalar: candidatos a un pase de
IA dirigido (no on toda la base, solo sobre estos huecos puntuales), que es la Fase 2 de este
proyecto si se decide implementarla.

## Re-ejecutar tras nuevas conversaciones

El script es idempotente — simplemente correrlo de nuevo regenera los 5 outputs desde cero, no hay
estado intermedio que mantener a mano.

## Próximos pasos sugeridos (no implementados en V1)

1. Pase de IA dirigido sobre `needs_ai_review.csv` para completar los 5 campos críticos.
2. Persistir `SECTOR`/`TIPO_PERFIL`/etc. de vuelta a `historial.json` o a los propios `.md`, para que
   las próximas conversaciones ya no dependan de heurística.
3. Usar las reglas derivadas de `RESULTADO_FINAL` por sector/cargo/variante (Etapa 4 del pedido
   original) para ajustar el SYSTEM prompt del generador — pero solo una vez que el volumen de datos
   por segmento sea suficiente (hoy la mayoría de sectores tiene 1-3 casos, insuficiente para
   conclusiones estadísticas sólidas).
