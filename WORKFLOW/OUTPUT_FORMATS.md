# OUTPUT_FORMATS.md — Formato Exacto de Salida

Todo output sigue este formato. Nunca mostrar solo el mensaje. Nunca mostrar solo el diagnóstico.

---

## FORMATO COMPLETO (default)

```
====================================================

PROSPECTO:
Nombre:
Empresa:
Cargo:

====================================================

ESTADO ACTUAL

Stage detectado:

Último mensaje enviado por Hint:

Último mensaje del prospecto:

Tiempo transcurrido:

====================================================

ANÁLISIS

Engagement:
LOW / MEDIUM / HIGH

Interés:
LOW / MEDIUM / HIGH

Señales detectadas:
-
-
-

Objeciones:
-
-

Oportunidades:
-
-

====================================================

DECISIÓN

Acción:
MSG2 / SEG1 / SEG2 / WAIT / RECOVERY

Estrategia:
CONSULTIVA / ENTRE_PARES / EXPLORATORIA

Motivo:
(máximo 5 líneas)

====================================================

INPUT DEL LLM

Qué debería lograr el mensaje:
-
-
-

Qué NO debería hacer:
-
-
-

Ángulo recomendado:

Pregunta recomendada:

CTA:

====================================================

MENSAJE

[Mensaje listo para copiar y pegar — sin etiquetas B1/B2/B3/B4]

====================================================
```

---

## REGLAS DE FORMATO

- Diagnóstico siempre antes del mensaje. Sin excepciones.
- El mensaje va sin etiquetas B1/B2/B3/B4 — solo texto plano por línea.
- Salto simple entre burbujas del MSG2. No línea en blanco.
- No explicar el mensaje después de mostrarlo. El mensaje habla solo.
- Si el output es WAIT o RECOVERY → no hay sección MENSAJE. Solo diagnóstico + recomendación.

---

## FORMATO REDUCIDO (solo cuando el usuario pide solo el mensaje)

Solo si el usuario explícitamente dice "dame solo el mensaje" o equivalente.

```
[Acción detectada] — [Prospecto]

[Mensaje listo para copiar]
```

---

## FORMATO GUARDADO (cuando el usuario dice "guarda")

```
Guardando...

✓ .md actualizado — ../conversaciones/julio/{slug}.md
✓ historial.json actualizado — stage "{n}" para {nombre}
✓ Commit linkedin-hintmedia master
✓ historial.json copiado a linkedin-historial
✓ Push linkedin-historial main
✓ Push linkedin-hintmedia master

Listo.
```
