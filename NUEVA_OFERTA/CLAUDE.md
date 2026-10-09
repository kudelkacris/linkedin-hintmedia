# CLAUDE.md — Nueva oferta: Capacitaciones + Videos de lanzamiento

Esta carpeta es una línea comercial aparte de la prospección de Florencia.
**Dentro de esta carpeta, estas reglas reemplazan a las del CLAUDE.md padre** en todo lo que sea MSG1, MSG2, target y clientes.
Del padre se mantienen: formato (sin ¿ ¡ ni guion largo), blocklist, "nunca atribuir al prospecto algo que no dijo", y el protocolo de leer antes de escribir.

Origen: llamada con el jefe del 05/10/26. El servicio integral es muy amplio y las empresas grandes cotizan a fin de año: se sale con dos productos puntuales.

---

## Cuenta y programa

- **Corrección 09/10/26:** es todo una misma cuenta con dos enfoques distintos (marketing integral y Capacitaciones + Videos). Las aceptadas de las dos tandas aparecen juntas en la lista de contactos: cruzar con `listas/2026-10-07-invitaciones-enviadas.md` para saber qué enfoque le toca a cada uno. Reglas de tono del MSG1 corto (pregunta cálida, sin "más adelante", sin dos puntos, obra del cliente ≠ trabajo nuestro): ver sección "TANDAS DE CONEXIONES ACEPTADAS" del CLAUDE.md padre.
- Programa: `python servidor.py` dentro de esta carpeta → **http://localhost:3001** (el de Florencia sigue en 3000).
- Historial propio: `NUEVA_OFERTA/historial.json`. Conversaciones: `NUEVA_OFERTA/conversaciones/<mes>/`.
- El programa avisa si el prospecto ya fue contactado desde la cuenta de Florencia (lee `../historial.json` sin modificarlo).
- La API key se toma de `.env.local` de esta carpeta o de la carpeta padre.

## Target (las dos líneas)

- **Tamaño:** empresas de 200 a 500+ empleados. Una empresa chica no tiene comunicación interna ni presupuesto de capacitación.
- **Sector: no importa** (decisión del 05/10/26). Lo único que filtra es que la empresa sea grande.
- **País:** Argentina primero. Perú, Colombia y Ecuador en segundo lugar.
- **Áreas:** RRHH, cultura, comunicación interna, comunicación corporativa.
- **Filtros en Sales Navigator:** tamaño de empresa 201-500 / 501-1000 / 1001-5000 / 5001+. Función: Recursos Humanos o Comunicación. Keywords: "comunicación interna", "cultura", "capacitación", "desarrollo organizacional".
- **Timing:** octubre a diciembre es cuando se arma el plan del año siguiente. Se usa como contexto, nunca como presión.

### Búsqueda en Sales Navigator (aprendido el 05/10/26)

El sector no importa: el filtro que manda es el **tamaño de empresa**.

**Búsqueda única**
- Tamaño de empresa: 201-500 / 501-1.000 / 1.001-5.000 / 5.001+. Es el filtro clave.
- Ubicación: Argentina
- Palabras clave: `"comunicación interna" OR cultura OR "marca empleadora" OR "employer branding" OR "comunicación corporativa" OR "relaciones institucionales" OR capacitación OR "desarrollo organizacional"`
- Nivel: Gerente, Director, Experimentado. Sin Entry ni Training.
- Activar **"Publicó en LinkedIn en los últimos 30 días"**: sin un hecho reciente no hay ancla para el B1.
- Excluir sectores que no compran esto: consultoras, agencias, universidades, organismos estatales que compran por licitación.

**Reglas al armar la lista**
- 1er grado = ya son contactos de esta cuenta, se les escribe directo.
- **Transener, TGS y Sullair son clientes**: nunca contacto en frío. Si aparece alguien de ahí, lo decide el jefe (puede ser una venta adicional).
- **Competidores directos de clientes** (TGN frente a TGS, por ejemplo): confirmar con el jefe antes de escribir.
- Una persona por empresa por vez. El segundo contacto de la misma empresa, solo si el primero no responde.
- Analistas y coordinadores: sí, pero el objetivo es que deriven al gerente.
- Las listas clasificadas quedan en `listas/AAAA-MM-DD-<búsqueda>.md`.

---

## LÍNEA 1 — Videos de lanzamiento

**Qué:** videos de 1 a 2 minutos con dos técnicas:
- motion graphics (After Effects + imágenes IA) para proyectos, obras e inversiones;
- ilustración animada para cultura, valores y liderazgo.

**Sub-ángulo PROYECTO**
- A quién: comunicación corporativa o externa, relaciones institucionales.
- Ancla: proyecto, obra o anuncio de la empresa (RIGI, Vaca Muerta, planta, ducto, mina).

**Sub-ángulo CULTURA**
- A quién: RRHH, cultura, comunicación interna, employer branding.
- Ancla: post sobre valores, cultura, liderazgo u onboarding.

**Pruebas que se pueden usar (solo estas):**
- TGS, ampliación del gasoducto Perito Moreno: motion graphics de la obra. Publicado.
- TGS, video de cultura: valores, liderazgo y sueño 2030 en ilustración. Se usó en redes y en comunicación interna. Publicado.
- Sullair, video institucional de lanzamiento. Publicado. Trajo trabajos nuevos.

**Prohibido:**
- El video de TGS de líquidos de Vaca Muerta (NGL, Bahía Blanca): **no se publicó todavía**. No se menciona hasta que salga.
- Decir que hicimos videos para Transener: pidieron presupuesto, no hay video.

**Material para el MSG2:** carpeta o pestaña con 3 o 4 videos publicados → `[LINK VIDEOS]` (pendiente, lo arma el jefe).

## LÍNEA 2 — Capacitaciones

**Qué:** capacitaciones para equipos internos:
- LinkedIn profesional: perfil, qué publicar, cómo contar el trabajo propio y el de la empresa.
- Vocería digital para gerentes y referentes.

**Facilitador:** con experiencia en empresas grandes del sector. **No nombrarlo** hasta que se confirme.

**A quién:** director o gerente de RRHH, capacitación, desarrollo organizacional, talento, cultura.
**Ancla:** post sobre capacitación, programa de líderes, marca empleadora o plan anual.

**Prueba que se puede usar (solo esta):** vocería digital de la gerencia de Transener y LinkedIn de TGS → "con eso armamos una capacitación…".
**Prohibido:** decir que ya capacitamos a un cliente. Inventar horas, personas o resultados.

**Material para el MSG2:** temario breve → `[LINK TEMARIO]` (pendiente, el jefe arma el dossier).

---

## MSG1 (las dos líneas)

3 burbujas, entre 60 y 85 palabras:

- **B1:** `[Nombre], gracias por conectar!` + el hecho dicho directo ("Vi que arrancaron…", "Leí lo de…", "Felicitaciones por…"). **Prohibido "Me llamó la atención"** (pedido del 05/10/26). **Para ahí.** Sin hablar de video, capacitación ni Hint, y sin comentario valorativo después del hecho.
- **B2:** una prueba real de la línea, con el cliente nombrado y solo los datos de la lista. Sin inventar dónde circuló ni qué resultados tuvo.
- **B3:** una pregunta de sí o no que nazca de B2. Ejemplos:
  - Proyecto: "Lo tienen pensado contar en video?"
  - Cultura: "Lo trabajan también en video hacia adentro?"
  - Capacitaciones: "Es algo que tienen en el plan de capacitación 2027?"

**Sin link en el MSG1.** El jefe propuso mandar los videos de entrada, pero los datos propios dicen que el pitch en el primer mensaje baja la respuesta al 8-17%. El link va en el MSG2. Si el jefe quiere probar link en el MSG1, medirlo aparte.

`CIERRE_USADO`: 1 = videos proyecto, 2 = videos cultura, 3 = capacitaciones.

## MSG2 (cuando responde)

- **Dijo que sí:** retomar su respuesta → cómo lo resolvimos con el cliente nombrado → ofrecer carpeta o temario con contexto + pedir permiso.
- **Dijo que no:** no insistir. Dejar el material para el plan del año que viene.
- **Preguntó precio:** no inventar números. "Depende de duración y técnica" (videos) o "de cantidad de personas y modalidad" (capacitaciones). Llamada por Google Meet, pedir mail. Nunca WhatsApp.
- **Derivó:** pedir nombre o contacto de esa persona.

## Stage map (igual que el padre)

1 MSG1 · 2 MSG2 · 3 material enviado · 4 SEG1 · 6 reunión. Campo `name`, stage como string, y además `linea` (`videos` / `capacitaciones`).

## Pendientes

- [ ] El jefe arma los dos dossiers (videos y capacitaciones).
- [ ] Link a la carpeta de videos publicados.
- [ ] Confirmar al facilitador de capacitaciones y el temario.
- [ ] Confirmar cuándo sale el video NGL de TGS para sumarlo como prueba.
- [ ] Sales Navigator en la cuenta del jefe (está viendo el costo).

---

## Búsqueda v2 en Sales Navigator (aprendido el 06/10/26)

Reemplaza a "Búsqueda única" de arriba. Lo que se probó y cómo quedó:

- **Base fija (decisores):** Empleados 1.001-5.000 / 5.001-10.000 / 10.001+ (501-1.000 solo en energía y minería). Argentina. Privada + Empresa pública. Nivel **Director, Vicepresidente, Gerente con experiencia**. **Sacar Sénior**: ahí caen analistas, HRBP y reclutadores.
- **Cargo actual** no acepta texto libre en la cuenta del jefe. Las palabras clave van en la caja de arriba, buscan en TODO el perfil (por eso entran consultores que "fueron" directores). Controlar con **Sector → excluir**: consultoría, servicios de RRHH, educación superior, administración gubernamental, publicidad.
- **Palabras clave RRHH:** `"director de recursos humanos" OR "directora de recursos humanos" OR "gerente de recursos humanos" OR "gerente de rrhh" OR "HR director" OR "head of people" OR "chief people officer" OR "director de capital humano"`
- **Energía y minería:** mismo cargo con `AND (energía OR minería OR petróleo OR "oil & gas" OR litio OR cobre OR eléctrica OR renovable)`. "Ha publicado en LinkedIn" apagado.
- **Comunicación / asuntos corporativos:** por palabras clave (`"asuntos corporativos" OR "relaciones institucionales" OR "comunicación corporativa" OR "corporate affairs" OR "public affairs"`), sin filtro de Función y sin "Ha publicado". Con Función salen casi solo Estado, medios y agencias. Mejor aún: buscar por lista de empresas.
- **Rinde:** RRHH grande da ~50% de útiles; energía y minería ~50%; comunicación por palabras clave ~10%.
- **No sirve para vender:** consultores y fractional, Vistage, coaches, docentes, universidades, Estado, agencias, venta de software de RRHH (Humand), reclutadores. Algunos sirven de aliados (conocen gerentes de RRHH).
- **Decisores no RRHH:** el video de proyecto lo decide comunicación, asuntos corporativos o gerencia general. En empresas medianas (200-1.000) el GG decide todo; en grandes ir al director de área, no al CEO (CEO en frío convierte 10% frente a 25%).
- **Antes de invitar:** cruzar con `../historial.json` (Florencia) y con `listas/2026-10-07-invitaciones-enviadas.md`. Una persona por empresa.
- Clientes (TGS, Transener, Sullair) y competidores de clientes (TGN, Aggreko): los decide el jefe. PECOM: Florencia tiene conversaciones abiertas.
