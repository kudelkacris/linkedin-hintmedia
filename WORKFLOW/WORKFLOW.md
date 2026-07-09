# WORKFLOW.md — Pipeline Obligatorio

No existe otro flujo. Sin excepciones.

---

## PIPELINE PRINCIPAL

```
INPUT: conversación pegada por el usuario
        ↓
[1] IDENTIFICAR PROSPECTO
    Leer nombre del prospecto en la conversación.
        ↓
[2] BUSCAR .md
    Buscar automáticamente ../conversaciones/julio/{slug}.md
    Si no existe → trabajar solo con la conversación.
        ↓
[3] LEER .md COMPLETO
    Señal humana, tensión, hipótesis, ángulo, MSG1 enviado, notas.
        ↓
[4] LEER CONVERSACIÓN COMPLETA
    Último mensaje de Hint. Último mensaje del prospecto. Timeline.
        ↓
[5] DETECTAR STAGE
    1 = MSG1 enviado
    2 = MSG2 enviado
    3 = Dossier enviado/confirmado
    4 = SEG1 enviado
    6 = Reunión confirmada
        ↓
[6] ANALIZAR ÚLTIMO MENSAJE DEL PROSPECTO
    ¿Qué información nueva apareció?
    ¿Qué emoción transmite?
    ¿Qué habilita esa respuesta?
        ↓
[7] ANALIZAR ENGAGEMENT
    LOW / MEDIUM / HIGH
    Velocidad de respuesta + tono + apertura + preguntas.
        ↓
[8] DETECTAR SEÑALES, OBJECIONES, OPORTUNIDADES
        ↓
[9] ELEGIR ACCIÓN
    MSG2 / SEG1 / SEG2 / WAIT / RECOVERY
        ↓
[10] ELEGIR ESTRATEGIA
     CONSULTIVA / ENTRE_PARES / EXPLORATORIA
     Ver clasificación en METODOLOGIA.md
        ↓
[11] CONSTRUIR DIAGNÓSTICO
     Según OUTPUT_FORMATS.md — sección DIAGNÓSTICO
        ↓
[12] GENERAR CONTEXTO PARA EL LLM
     Qué debe lograr. Qué no debe hacer. Ángulo. Pregunta. CTA.
        ↓
[13] ESCRIBIR MENSAJE
     Según el archivo PROMPTS/{ACCIÓN}.md correspondiente.
        ↓
[14] REVISAR BLOCKLIST
     Leer BLOCKLIST.md y verificar cada ítem.
        ↓
[15] EJECUTAR CHECKLIST
     Leer CHECKLIST.md y verificar cada ítem.
     Si algún ítem es NO → reescribir. No mostrar.
        ↓
OUTPUT: Diagnóstico + Mensaje según OUTPUT_FORMATS.md
```

---

## PIPELINE DE GUARDADO

Cuando el usuario dice "guarda" o equivalente:

```
[1] Actualizar .md del contacto en ../conversaciones/julio/
    Agregar respuesta MSG1, MSG2 o SEG1. Cambiar Estado.
        ↓
[2] Actualizar ../historial.json
    Buscar por campo `name` (no `nombre`).
    Actualizar TODAS las entradas que matcheen.
    Stage como string ("2", "3", etc.)
        ↓
[3] Commit a linkedin-hintmedia (rama master)
        ↓
[4] Copiar historial.json a C:\Users\neces\Desktop\CLAUDE\linkedin-historial\
    Commit + push rama main
        ↓
[5] Push linkedin-hintmedia master
```

**Stage map:**
- MSG1 enviado = "1"
- MSG2 enviado = "2"
- Dossier enviado = "3"
- SEG1 enviado = "4"
- Reunión agendada = "6"

---

## REGLAS DEL PIPELINE

- Nunca saltear pasos.
- Si el prospecto hizo una pregunta, responderla antes de avanzar al pitch.
- Si el dossier ya fue enviado y no hay respuesta → SEG1 directo, no preguntar qué hacer.
- Si el prospecto acepta reunión → pedir mail + Google Meet. Nunca WhatsApp.
- El diagnóstico siempre se muestra antes del mensaje.
