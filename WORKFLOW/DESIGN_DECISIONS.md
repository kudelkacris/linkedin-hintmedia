# DESIGN_DECISIONS.md — Por qué el sistema funciona así

Este archivo documenta las decisiones de diseño que no deben modificarse sin entender el razonamiento detrás.

---

## Por qué el LLM no decide

El LLM improvisa. Cuando no tiene estructura, inventa. Cuando tiene instrucciones genéricas, las aplica a medias.

El CRE (Commercial Reasoning Engine) existe para que todas las decisiones comerciales sean deterministas:
- Qué acción tomar (MSG2 / SEG1 / SEG2 / WAIT)
- Qué estrategia usar (CONSULTIVA / ENTRE_PARES / EXPLORATORIA)
- Qué ángulo de valor usar (rotación obligatoria)
- Si el mensaje puede salir o no (review)

El LLM recibe un contexto construido por el motor y solo redacta. No elige.

---

## Por qué existe el diagnóstico antes del mensaje

Sin diagnóstico, el LLM genera el primer mensaje que se le ocurre y el usuario no tiene forma de saber si fue la decisión correcta.

El diagnóstico hace visible el razonamiento. Si el diagnóstico está mal, el usuario puede corregirlo antes de que se escriba el mensaje. Eso es imposible si el mensaje llega primero.

---

## Por qué el Workspace tiene prioridad sobre el chat

El chat no persiste. El Workspace sí.

La metodología comercial de Hint Media tardó meses en construirse. Si vive solo en el chat, se pierde con cada sesión. Si vive en archivos, cualquier IA puede ejecutarla mañana sin que nadie tenga que explicar nada.

---

## Por qué el diagnóstico es obligatorio incluso para mensajes simples

Porque el mensaje "simple" que parece obvio muchas veces tiene:
- Un ángulo que ya se usó (y repetirlo es un error)
- Una objeción implícita que hay que manejar antes del CTA
- Un nivel de seniority que define si el tono debe ser consultivo o entre pares

Lo que parece simple desde afuera es una decisión comercial con consecuencias. El diagnóstico hace esas decisiones explícitas.

---

## Por qué el CRE está separado del programa web

El CRE es el motor de razonamiento. El programa web (index.html + servidor.py) es la interfaz de trabajo diario.

Si el CRE estuviera acoplado al programa, cambiar el LLM requeriría reescribir el programa. Así, si mañana Hint Media pasa de Claude a GPT, solo cambia el adapter del CRE. Nada más.

---

## Por qué MSG1 no menciona Hint

Porque la función de MSG1 es exclusivamente generar curiosidad para que el prospecto responda.

Si MSG1 menciona Hint, el prospecto evalúa si quiere hablar con una agencia antes de conocer a Florencia. Eso cierra la conversación antes de abrirse.

MSG1 abre. MSG2 presenta. Son roles distintos.

---

## Qué no debe modificarse nunca sin revisión profunda

- La secuencia MSG1 → MSG2 → SEG1 → SEG2 (cada uno tiene un rol único)
- La regla de que el primer sujeto no puede ser "nosotros" o "Hint"
- La regla de rotación de valor en SEG1
- La jerarquía de fuentes (Workspace > conversación > .md > pedido del usuario)
- La frase fija del CTA del dossier
