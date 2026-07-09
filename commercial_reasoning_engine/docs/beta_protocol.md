# Beta Protocol v1.0
## Metodología oficial de validación del CRE

**Vigencia:** CRE v1.0  
**Estatus:** Documento constitucional — mismo nivel de autoridad que `ARCHITECTURE_LOCK.md`  
**Regla de versionado:** Ninguna modificación silenciosa. Toda actualización genera una nueva versión (Beta Protocol v1.1, v2.0, etc.) y documenta el motivo del cambio.

---

## 1. Objetivo de la Beta

La Beta **no busca aumentar el porcentaje de PASS del Reviewer.**

Busca identificar el módulo raíz responsable de cada diferencia entre la decisión del CRE y el criterio humano.

La pregunta central de cada caso no es:

> "¿Pasó o falló?"

Sino:

> "¿Qué módulo tomó la primera decisión incorrecta?"

El objetivo es corregir el módulo más temprano posible del pipeline. Nunca modificar un módulo posterior para compensar un error de uno anterior.

---

## 2. Dataset congelado

El benchmark oficial de la Beta está compuesto por exactamente **10 conversaciones heterogéneas**.

Composición obligatoria:

| # | Tipo |
|---|------|
| 001, 002 | MSG2 |
| 003, 004 | SEG1 — engagement LOW |
| 005, 006 | SEG1 — engagement HIGH |
| 007, 008 | SEG2 |
| 009, 010 | Casos borde (edge cases) |

**Regla:** Este dataset no cambia durante toda la Beta ni entre versiones. Todas las versiones futuras del CRE deben ejecutarse contra exactamente las mismas 10 conversaciones para mantener comparabilidad. Un resultado del CRE v1.1 solo es válido si se corrió contra `beta_dataset/001.md` a `010.md` sin modificaciones.

Ubicación: `commercial_reasoning_engine/beta_dataset/`

---

## 3. CSV oficial de evaluación

El CSV de evaluación es una capa separada del Decision Log. El Decision Log registra lo que decidió el motor. El CSV registra la evaluación humana. Nunca deben mezclarse.

**Columnas exactas (no agregar ni quitar):**

```
Caso | Resultado CRE | Florencia hubiera escrito | Categoría | Módulo raíz | Diagnóstico
```

**Categorías permitidas:**

| Categoría | Descripción |
|-----------|-------------|
| `PASS` | El motor y el criterio humano coinciden |
| `EXPECTED FAIL` | El Reviewer rechazó correctamente un draft malo |
| `FALSE POSITIVE` | El Reviewer bloqueó un mensaje que el criterio humano hubiera aprobado |
| `FALSE NEGATIVE` | El Reviewer dejó pasar un mensaje que el criterio humano hubiera rechazado |

**Módulos raíz permitidos:**

```
Analyzer | Evidence | Classifier | Strategy | Context | LLM | Reviewer
```

El campo `Módulo raíz` se completa solo cuando la categoría es `FALSE POSITIVE` o `FALSE NEGATIVE`. Para `PASS` y `EXPECTED FAIL` se deja vacío.

---

## 4. Regla de depuración

Cuando aparece un error, recorrer el pipeline en orden hacia atrás desde el síntoma:

```
Reviewer
  ← Context Builder
    ← Strategy Builder
      ← Classifier
        ← Evidence Engine
          ← Analyzer
```

La causa se asigna al primer módulo que tomó una decisión incorrecta. No al módulo donde el error se volvió visible.

**Nunca** modificar un módulo posterior para compensar un error de uno anterior.

Ejemplo: si el Reviewer rechaza un draft que el criterio humano hubiera aprobado, la pregunta no es "¿es el Reviewer demasiado estricto?" La pregunta es "¿el Context Builder entregó suficientes `allowed_claims`? ¿El Strategy Builder eligió bien el ángulo? ¿El Evidence Engine dejó pasar suficiente evidencia real?"

El Reviewer debe mantenerse conservador. El estándar del Reviewer no se baja para aumentar el porcentaje de PASS.

---

## 5. Política de cambios durante la Beta

**Durante la Beta, queda prohibido modificar el código después de un caso individual.**

El flujo es:

1. Correr los 10 casos completos.
2. Completar el CSV de evaluación para los 10.
3. Agrupar los errores por módulo raíz.
4. Si cinco errores distintos tienen la misma causa, recién entonces se modifica el módulo correspondiente.

No se corrige "en caliente". Un caso individual no es evidencia suficiente para cambiar una regla.

---

## 6. Excepción crítica — FALSE NEGATIVE

Los `FALSE NEGATIVE` tienen prioridad absoluta sobre la política de cambios.

Si el Reviewer deja pasar cualquiera de los siguientes:

- Frase de blocklist ("Retomo...", "Quedo atenta", "Gracias por la apertura", etc.)
- Violación de perspectiva (primer sujeto del mensaje es Hint, no el prospecto)
- Uso de `forbidden_claims` como hechos afirmados

Entonces:

1. Se documenta inmediatamente en el CSV con categoría `FALSE NEGATIVE`.
2. Se abre un issue crítico separado.
3. Se puede corregir el módulo antes de completar los 10 casos.

Estos bugs pueden corregirse antes de finalizar la Beta porque representan una falla de seguridad del sistema, no un ajuste de calibración.

---

## 7. Criterio de aceptación para modificar un módulo

Antes de implementar cualquier cambio en cualquier módulo, responder estas dos preguntas:

1. **¿Esto es un problema de arquitectura o de reglas comerciales?**  
   Si es de reglas comerciales, el cambio va a una regla o a un prompt. No a la estructura del módulo.

2. **¿Qué evidencia del benchmark demuestra que hace falta cambiarlo?**  
   Si no hay evidencia en el dataset de 10 conversaciones, no se cambia el motor.

Una impresión, una intuición, o un caso externo al benchmark no son criterio suficiente para modificar un módulo durante la Beta v1.0.

---

## 8. Versionado del protocolo

Este documento queda congelado junto con `ARCHITECTURE_LOCK.md`.

Para modificar este protocolo:

1. Crear `beta_protocol_v1.1.md` (o la versión correspondiente).
2. Documentar qué cambió y por qué.
3. El documento anterior no se edita ni se elimina — queda como referencia histórica.

Nunca editar silenciosamente el documento vigente.

---

*Beta Protocol v1.0 — Aprobado para CRE v1.0*
