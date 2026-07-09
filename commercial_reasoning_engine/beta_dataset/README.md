# Beta Dataset — CRE v1.x Benchmark Oficial

Este dataset constituye el benchmark oficial del CRE v1.x.

Las conversaciones no deben modificarse durante la Beta.

Todas las versiones futuras del CRE deberán ejecutarse sobre exactamente este dataset para mantener comparabilidad.

---

## Composición

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| 001_msg2_low.md | MSG2 | Prospecto respondió con pocas palabras, engagement bajo |
| 002_msg2_medium.md | MSG2 | Prospecto respondió con interés moderado |
| 003_seg1_low.md | SEG1 LOW | Dossier enviado, sin respuesta, poco intercambio previo |
| 004_seg1_high.md | SEG1 HIGH | Dossier enviado, sin respuesta, entusiasmo previo claro |
| 005_seg2.md | SEG2 | SEG1 enviado sin respuesta, proponer reunión o cerrar ciclo |
| 006_edge_case.md | Edge | Caso borde: prospecto cerró con objeción |
| 007_msg2_high.md | MSG2 | Prospecto respondió con entusiasmo o pregunta puntual |
| 008_seg1_medium.md | SEG1 MEDIUM | Dossier enviado, intercambio real previo, sin respuesta |
| 009_recovery.md | Edge | Caso borde: conversación interrumpida o respuesta tardía |
| 010_complex_case.md | Complex | Caso complejo: múltiples señales contradictorias |

## Reglas

- No agregar conversaciones al dataset durante la Beta v1.0.
- No modificar conversaciones existentes.
- Para la Beta v1.1 o posteriores, crear un dataset nuevo en `beta_dataset_v1.1/`.

## Referencia

Ver `docs/beta_protocol.md` — Sección 2: Dataset congelado.
