# DESIGN_DECISIONS.md — Por qué el CRE es como es

Este documento registra las decisiones de diseño que podrían parecer extrañas meses después.
No es documentación de código. Es documentación de principios.

Cada sección responde una pregunta que alguien va a hacer cuando quiera "optimizar" el sistema.
Leer este documento antes de cambiar cualquier decisión estructural.

---

## 1. ¿Por qué el Reviewer tiene autoridad sobre el LLM?

**Decisión:** El Reviewer puede rechazar un draft generado por el LLM. El LLM no puede apelar esa decisión.

**Por qué:** El LLM es un redactor. No tiene acceso a las reglas comerciales completas, al historial de errores, ni a la blocklist. El Reviewer sí. Dar autoridad al LLM sobre su propio output crea un sistema donde el modelo evalúa su propio trabajo, que es exactamente el problema que el CRE existe para resolver.

**La inversión que importa:**
- Antes del CRE: Claude decide, Claude redacta, Claude evalúa.
- Con el CRE: CRE decide, Claude redacta, CRE evalúa.

**Consecuencia de romper esta decisión:** Si el Reviewer se debilita para aumentar el porcentaje de PASS, el sistema vuelve a ser una caja negra con prompt largo.

---

## 2. ¿Por qué el LLM nunca ve la conversación completa?

**Decisión:** El LLM recibe únicamente un `LLMContext` — un objeto serializado con prospecto, tono, objetivo, estructura, claims permitidos y prohibidos. Nunca recibe el texto crudo de la conversación.

**Por qué:** Si el LLM recibe la conversación completa, empieza a razonar sobre ella. Y si razona sobre ella, empieza a tomar decisiones comerciales: qué ángulo usar, qué mencionar, qué omitir. Esas decisiones pertenecen al motor, no al modelo.

El `LLMContext` es la única interfaz entre el razonamiento comercial y la generación de texto. Es deliberadamente estrecho.

**Consecuencia de romper esta decisión:** El LLM empieza a compensar gaps del motor. Los errores se vuelven invisibles porque el modelo los oculta con texto bien redactado.

---

## 3. ¿Por qué el Evidence Checker es conservador?

**Decisión:** El Evidence Checker prefiere rechazar un draft correcto (falso positivo) antes que dejar pasar un draft con claims inventados (falso negativo).

**Por qué:** Un claim inventado que llega al prospecto es un error de credibilidad. El prospecto puede detectarlo ("nunca dije eso"), y la consecuencia es que la conversación muere. Un draft rechazado por ser demasiado conservador es un error de eficiencia: el sistema pide mejoras al Context Builder o al Strategy Builder.

Los falsos positivos son ruido. Los falsos negativos son riesgo.

**Consecuencia de romper esta decisión:** Si el Evidence Checker se relaja "porque el LLM generalmente acierta", se acumulan casos donde el modelo afirma cosas como hechos que solo existen en `forbidden_claims`. Esos errores son difíciles de detectar porque el texto suena correcto.

---

## 4. ¿Por qué el Strategy Builder decide antes del prompt?

**Decisión:** El Strategy Builder construye la decisión comercial completa (qué mencionar, qué omitir, qué ángulo usar, si proponer reunión) antes de que el LLM vea cualquier instrucción.

**Por qué:** Si la decisión comercial se delega al prompt, el sistema depende del modelo para aplicarla correctamente. Cada cambio de modelo requiere re-validar si la decisión se sigue tomando bien. Al separar la decisión del prompt, el motor es independiente del modelo.

**Prueba del diseño:** Si mañana se reemplaza `ClaudeAdapter` por `GPTAdapter`, el Strategy Builder no cambia. Ni el Reviewer. Ni el Classifier. Solo cambia el adaptador.

**Consecuencia de romper esta decisión:** La lógica comercial migra al prompt, el sistema se vuelve dependiente del modelo, y cualquier actualización del modelo puede cambiar el comportamiento comercial silenciosamente.

---

## 5. ¿Por qué el motor prefiere un falso positivo antes que un falso negativo?

**Decisión:** En todos los módulos evaluadores (Evidence Engine, Reviewer), el error preferido es bloquear algo correcto antes que dejar pasar algo incorrecto.

**Por qué:** El costo asimétrico. Un mensaje bloqueado incorrectamente puede revisarse. Un mensaje incorrecto que llega al prospecto no puede deshacerse. La reputación de Hint Media en una conversación de LinkedIn no tiene undo.

**Cuándo revisar esta decisión:** Si el porcentaje de falsos positivos sube por encima del 20% de los casos, hay un problema de calibración que vale la pena investigar. Pero la dirección del sesgo no cambia: siempre hacia el falso positivo.

---

## 6. ¿Por qué cada módulo tiene una sola responsabilidad?

**Decisión:** Cada módulo hace exactamente una cosa. El Analyzer no clasifica acciones. El Classifier no construye estrategias. El Strategy Builder no redacta.

**Por qué:** Cuando un error aparece, la pregunta es "¿en qué módulo ocurrió?". Si los módulos mezclan responsabilidades, la respuesta es "no sé". La responsabilidad única hace que el tiempo hasta el módulo raíz sea predecible.

**Consecuencia de romper esta decisión:** El KPI de "tiempo hasta módulo raíz < 10 min" deja de ser alcanzable. El sistema vuelve a ser opaco.

---

## 7. ¿Por qué el Decision Log registra el trace completo y no solo el resultado?

**Decisión:** Cada run persiste el output de todos los módulos, no solo el mensaje final.

**Por qué:** El mensaje final es el síntoma. El trace es el diagnóstico. Sin el trace, reproducir un error requiere reconstruir el contexto manualmente. Con el trace, el diagnóstico empieza en el JSON.

**Consecuencia de romper esta decisión:** Los errores en producción se vuelven irreproducibles. El tiempo de diagnóstico sube.

---

## Regla para modificar estas decisiones

Ninguna de las decisiones de este documento debe cambiarse por intuición, por presión de velocidad, o porque "parece que el LLM lo haría mejor".

Para modificar una decisión:

1. Identificar qué evidencia del benchmark demuestra que la decisión produce peores resultados que la alternativa.
2. Proponer la alternativa concretamente.
3. Correr el benchmark con la alternativa.
4. Si mejora: actualizar este documento con la nueva decisión y el motivo del cambio.
5. Si no mejora: documentar el experimento aquí de todas formas.

El historial de decisiones descartadas vale tanto como el de las adoptadas.

---

*DESIGN_DECISIONS v1.0 — CRE v1.0*
