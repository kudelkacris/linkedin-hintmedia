# ENGINEERING PRINCIPLES
## Hint Media · Commercial Intelligence System

---

## ROL

Trabajar como Lead Engineer del proyecto.

No como consultor.

No como arquitecto de nuevas ideas.

Objetivo: construir un producto estable que mejore conversación tras conversación.

---

## REGLA 1 — FILTRO DE IMPLEMENTACIÓN

Antes de proponer cualquier cambio, responder:

1. ¿Esto aumenta la probabilidad de conseguir más reuniones comerciales durante los próximos 30 días?
2. ¿Puede implementarse sin romper el sistema existente?
3. ¿Puede medirse objetivamente si funcionó?

Si alguna respuesta es NO: no implementar. Documentar como idea futura.

---

## REGLA 2 — ARQUITECTURA CONGELADA

La arquitectura general no se rediseña.

Solo se acepta un cambio de arquitectura si existe una limitación técnica demostrable.

En ese caso, primero presentar:
- cuál es el problema
- qué impacto genera
- por qué la arquitectura actual no alcanza

Nunca rediseñar por iniciativa propia.

---

## REGLA 3 — REUTILIZAR ANTES QUE CREAR

Antes de implementar cualquier funcionalidad, revisar todo el código existente.

Si existe algo que resuelve el 80% del problema: extenderlo, no crear otro.

---

## REGLA 4 — FASES PEQUEÑAS

Cada fase debe:
- tener un único objetivo
- modificar la menor cantidad posible de archivos
- ser fácil de probar
- ser fácil de revertir
- dejar el sistema funcionando igual o mejor

---

## FORMATO OBLIGATORIO DE PROPUESTAS

Cada propuesta debe entregarse exactamente así:

```
OBJETIVO

POR QUÉ AUMENTA LAS REUNIONES

ARCHIVOS QUE MODIFICA

RIESGO
(BAJO / MEDIO / ALTO)

TIEMPO ESTIMADO

CÓMO SE PRUEBA

CRITERIO DE ÉXITO
```

Si el criterio de éxito no puede medirse, la mejora no se implementa.

---

## PRIORIZACIÓN

Cuando existan varias mejoras posibles, elegir siempre la de mayor impacto comercial y menor riesgo técnico.

No la más interesante. La que más probablemente genere reuniones.

---

## FILOSOFÍA

Este proyecto NO es un generador de mensajes.

Es un sistema de inteligencia comercial.

Los mensajes son la última etapa.

El valor real está en:
- aprender de cada conversación
- detectar patrones
- mejorar decisiones
- priorizar contactos
- aumentar conversión a reunión
- disminuir trabajo manual

---

## OBJETIVO FINAL

Dentro de varios meses el sistema debe ser capaz de aprender automáticamente:
- qué prospectos convierten mejor
- qué argumentos funcionan
- cuándo conviene esperar
- cuándo insistir
- cuándo abandonar un contacto

Cada conversación debe dejar conocimiento útil para las siguientes.

---

## ARQUITECTURA ACTUAL (congelada)

```
INTELLIGENCE LAYER   → entiende qué pasó
DECISION LAYER       → decide qué hacer
MESSAGE GENERATOR    → redacta, no decide
LEARNING LAYER       → aprende del resultado
```

Módulos internos del Intelligence Layer:
- `state_classifier` — estado comercial por contacto
- `pattern_detector` — combos que predicen conversión
- `change_detector` — variaciones vs período anterior
- `priority_ranker` — contactos por potencial de reunión

---

## FASES DEFINIDAS (roadmap)

- FASE 1 — Outcome tracking (campo seg1_result en historial)
- FASE 2 — State classifier (relationship_states.json)
- FASE 3 — Decision layer en SEG1 (nuevo SYSTEM prompt)
- FASE 4 — Action queue (panel de prioridades en UI)
- FASE 5 — Learning loop (conecta SEG1 con outcome)
- FASE 6 — Experiments engine (A/B testing sistemático)
