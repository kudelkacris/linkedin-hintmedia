# Proyecto 1 — Routing por calidad de respuesta
**Enfoque:** Tratar distinto a quien responde poco vs. quien ya habla

---

## El problema

El sistema trata todas las respuestas de MSG1 como si fueran iguales. Un "dale, contame" y un párrafo donde el prospecto comparte su situación real reciben el mismo MSG2. Eso es un error operativo con consecuencias directas: al prospecto que respondió con 4 palabras le llega un pitch de 4 burbujas antes de haber tenido una sola oración de intercambio real. La conversación se corta o se enfría.

---

## La propuesta

Antes de escribir MSG2, clasificar la respuesta de MSG1 en uno de tres niveles:

**FRÍO** (≤ 5 palabras, sin contexto propio):  
"dale", "claro", "adelante", "decime", "qué pregunta"

**TIBIO** (responde con algo pero no comparte situación propia):  
"Hola Florencia, gracias por el mensaje, claro con gusto"

**CALIENTE** (comparte situación real, hace una pregunta, muestra interés genuino):  
Respuesta de más de 25 palabras donde habla de su trabajo, contexto o hace una pregunta propia

---

## Flujo nuevo

```
MSG1
  └─ FRÍO → MSG1.5 (pregunta puente, sin Hint) → respuesta → MSG2
  └─ TIBIO → MSG2 estándar, B1 trabaja más duro
  └─ CALIENTE → MSG2 comprimido, llegar antes al dossier
```

**MSG1.5 — qué es:**  
Un solo mensaje, sin mencionar Hint, sin dossier. Objetivo único: hacer UNA pregunta que abra la conversación.

Ejemplo para alguien que respondió "claro" a un MSG1 sobre liderazgo de equipos:  
*"Curioso, es algo que estás resolviendo actualmente o más bien ya lo tenés aceitado?"*

Solo con la respuesta a esa pregunta se genera MSG2.

---

## Trade-off

**A favor:** el prospecto ya habló algo antes de recibir el pitch. MSG2 llega en un contexto de conversación real, no de frío. La tasa de respuesta a MSG2 debería subir.

**En contra:** agrega un paso en el 30-40% de las conversaciones (las que responden frío). Más volumen de mensajes a gestionar. Si MSG1.5 no es específico, suena a stalling y el prospecto lo detecta.

---

## Por dónde empezar

Implementar solo para respuestas FRÍO. Las TIBIO y CALIENTE siguen igual. Medir durante 2 semanas si la respuesta a MSG2 sube en el grupo que pasó por MSG1.5.
