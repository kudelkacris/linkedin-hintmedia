# ENGINE_PHILOSOPHY.md — Filosofía del CRE

Este documento no habla de código.
Habla de por qué existe el CRE y qué principios gobiernan su evolución.

Leerlo antes de proponer cualquier cambio estructural.

---

## El CRE existe para reducir incertidumbre

No para escribir mejor.
No para usar IA.
No para automatizar.

Para reducir incertidumbre.

Antes del CRE, la pregunta después de un error era: "¿Por qué Claude escribió eso?"
La respuesta era: no sabemos. Cambiemos el prompt.

Con el CRE, la pregunta es: "¿Qué módulo tomó la primera decisión incorrecta?"
La respuesta es localizable, explicable y corregible.

Esa es la razón de existir del motor.

---

## El LLM nunca piensa. El motor piensa. El LLM escribe.

El LLM es un redactor, no un razonador.

El motor decide:
- qué acción tomar (MSG2, SEG1, SEG2, WAIT)
- qué estrategia usar (CONSULTIVA, ENTRE PARES, EXPLORATORIA)
- qué mencionar y qué omitir
- qué ángulo comercial aplicar
- si proponer reunión

El LLM recibe esas decisiones ya tomadas y las convierte en texto.

Si mañana Claude se reemplaza por GPT, Gemini o DeepSeek, el comportamiento comercial debe permanecer idéntico. Solo cambia el adaptador.

---

## Criterio para aceptar cualquier mejora

Cada mejora debe disminuir una de estas dos cosas:

1. **Incertidumbre** — el motor toma mejores decisiones comerciales
2. **Tiempo de diagnóstico** — cuando algo falla, se encuentra más rápido

Si una propuesta no mejora ninguna de las dos, no entra.

No importa si el texto suena mejor.
No importa si el porcentaje de PASS sube.
No importa si parece una mejora obvia.

Si no reduce incertidumbre ni tiempo de diagnóstico, no es una mejora del CRE.

---

## El Reviewer es una barrera de seguridad, no una herramienta de calidad

El Reviewer puede bloquear mensajes excelentes.

Eso es preferible a dejar pasar uno que viole la blocklist, use claims inventados, o empiece desde el mundo de Hint en lugar del mundo del prospecto.

El costo de un mensaje bloqueado incorrectamente es operativo: hay que revisar el Context Builder o el Strategy Builder.

El costo de un mensaje incorrecto que llega al prospecto es reputacional: la conversación muere y no tiene undo.

El sesgo del Reviewer es permanente: falso positivo antes que falso negativo.

---

## La Beta no sirve para entrenar. Sirve para descubrir.

No buscamos demostrar que el motor funciona.
Buscamos descubrir dónde falla.

Un resultado de 10/10 en el primer benchmark no sería una buena señal. Significaría que elegimos conversaciones demasiado fáciles.

Los casos del benchmark deben ser los que históricamente causaron más problemas, no los que el motor resuelve bien.

---

## Nunca se cambia una regla por un caso individual

Se cambia cuando una categoría completa demuestra un patrón.

Ejemplo incorrecto:
> "El caso 006 falló. Vamos a modificar el Evidence Checker."

Ejemplo correcto:
> "Tres de diez casos fallaron en el Evidence Checker por la misma causa. Hay un patrón. Modificamos."

Un caso es un dato. Un patrón es evidencia. Solo la evidencia justifica un cambio.

---

## La arquitectura es más valiosa que el benchmark

Los tests son una red de seguridad.
El benchmark es un espejo.
La arquitectura es la razón de que ambos funcionen.

Si alguna vez hay que elegir entre mejorar el porcentaje de PASS y preservar la separación de responsabilidades entre módulos, se preserva la arquitectura.

Un motor con 9/10 en el benchmark y arquitectura limpia es mejor que un motor con 10/10 y módulos acoplados.

---

*ENGINE_PHILOSOPHY v1.0 — CRE v1.0*
