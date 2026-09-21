# Scripts de análisis

Herramientas usadas para el informe de septiembre 2026. Sirven para repetir el análisis cualquier mes sin rehacer el trabajo.

Todos leen desde `conversaciones/<mes>/*.md` y `historial.json`. Ninguno modifica datos salvo `fix_historial.py`.

## Orden de uso

**1. `analiza.py`** — el primero y obligatorio. Parsea las conversaciones, clasifica sector, país, género y seniority, y genera `rows.json`, que es el dataset que usan todos los demás. Ejecutarlo antes que cualquier otro.

**2. `analiza2.py`** — embudo por mes y cortes por género, seniority, sector, país y confidence.

**3. `analiza3.py`** — control de sesgo por cohorte, longitud del mensaje contra conversión, y clasificación de lo que contestaron los prospectos.

**4. `analiza4.py`** — impacto de cambios de metodología: antes y después de una fecha de corte, efecto de mencionar la agencia en el primer mensaje, y embudo post-dossier.

**5. `analiza5.py`** — tipos de ángulo, tipos de cierre y curiosidades.

**6. `analiza6.py`** — mide si un cierre concreto genera rechazo o apertura, mirando el texto de las respuestas.

## Language Bank

**`bank.py`** clasifica las conversaciones por resultado verificado (reunión, contacto, charla, murió) y calcula el vocabulario diferencial entre las que funcionaron y las que no. Genera `bank_raw.json`.

**`mkbank.py`** convierte eso en `HINT_LANGUAGE_BANK.md`, el archivo que alimenta los ejemplos del prompt.

## Informes

**`deck.py`** es el helper de estilo: paleta, tablas, barras, tarjetas. Los dos generadores lo importan.

**`informe1.py`** arma el deck de análisis. **`informe2.py`**, el de plan de acción. Ambos escriben en `SEPTIEMBRE INFORME/`.

**`valida.py`** revisa un `.pptx` y avisa si algo se sale de la diapositiva o si un texto no entra en su caja. Correrlo después de generar.

## Utilidades

**`fix_historial.py`** normaliza `historial.json`: genera los `id` faltantes sin colisionar, unifica `stage` a string y convierte fechas ISO al formato `dd/mm/aa`. Hace backup antes y verifica campo por campo que no se pierda nada. **Es el único script que escribe sobre los datos.**

**`cmp.py`** compara dos modelos generando con el mismo prompt y los mismos perfiles, y mide cumplimiento de reglas y costo. Pendiente de correr: requiere crédito de API.

## Advertencia

`cmp.py` y `test_ancla.py` (que está en la raíz) **consumen créditos de la API**. Cada corrida son entre 10 y 40 llamadas de unos 17.000 tokens de entrada. No los ejecutes sin querer.
