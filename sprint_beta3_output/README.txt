Sprint Beta 3 — Evaluacion manual de calidad LLM
=================================================

Fecha: 2026-07-09
Casos: 15
Exportados: 15
Bloqueados: 0

Como evaluar
------------

1. Abrir cada archivo .txt en esta carpeta.
2. Copiar TODO el contenido (template + contexto) y pegarlo en el LLM que estes usando:
   - Claude Code: pegar directo en el chat
   - ChatGPT: pegar en una nueva conversacion
   - Ollama: ollama run <modelo> < <archivo>.txt
3. Copiar la respuesta del LLM.
4. Evaluar con la rubrica:

Rubrica (puntuacion /10 por criterio):
  - Apertura (B1): conecta con la respuesta del prospecto?
  - Rapport: usa palabras del prospecto, iguala tono emocional?
  - Naturalidad: suena humano o parece un template?
  - Fluidez: las burbujas transicionan sin saltos?
  - Curiosidad: da ganas de seguir leyendo?
  - Personalizacion: podria ser para cualquier otro prospecto?
  - Pregunta final: es especifica o generica?
  - Parece Florencia?: nivel de proximidad al estilo real

Total: /80

Casos en esta carpeta:
  01. Andrés Cortés Andrade [OTHER / Marketing] — OK
  02. Pedro Andrés Miranda Borie [MANAGER / Tech] — OK
  03. José Pablo Cáceres Aguirre [MANAGER / Otro] — OK
  04. Richard Sandi Campos [DIRECTOR / Salud] — OK
  05. Catalina Pavia [MANAGER / Energia] — OK
  06. Huanda Aguilar [MANAGER / Retail] — OK
  07. Laura Tomas Palau [MANAGER / Otro] — OK
  08. Maria Belen Benitez [OTHER / Educacion] — OK
  09. Sebastián Estévez [MANAGER / Finanzas] — OK
  10. Gabriela Hidalgo Castro [OTHER / Retail] — OK
  11. Carolina Mendoza [MANAGER / Otro] — OK
  12. Daniela Leitón Salazar [OTHER / Otro] — OK
  13. David Spaggiari [CEO / Salud] — OK
  14. Ana Maria Urrea G [OTHER / Marketing] — OK
  15. Carolina Cabrera [OTHER / Energia] — OK
