# Beta Dataset — CRE v1.x Benchmark Oficial

Este dataset constituye el benchmark oficial del CRE v1.x.

Las conversaciones no deben modificarse durante la Beta.

Todas las versiones futuras del CRE deberán ejecutarse sobre exactamente este dataset para mantener comparabilidad.

---

## Composición

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| 001_msg2_low.md | MSG2 LOW | Prospecto respondió con pocas palabras, engagement bajo |
| 002_msg2_medium.md | MSG2 MEDIUM | Prospecto respondió con interés moderado |
| 003_msg2_high.md | MSG2 HIGH | Prospecto respondió con entusiasmo o pregunta puntual |
| 004_seg1_low.md | SEG1 LOW | Dossier enviado, sin respuesta, poco intercambio previo |
| 005_seg1_medium.md | SEG1 MEDIUM | Dossier enviado, intercambio real previo, sin respuesta |
| 006_seg1_high.md | SEG1 HIGH | Dossier enviado, sin respuesta, entusiasmo previo claro |
| 007_seg2.md | SEG2 | SEG1 enviado sin respuesta, proponer reunión o cerrar ciclo |
| 008_recovery.md | Edge | Conversación interrumpida o respuesta tardía |
| 009_edge_case.md | Edge | Prospecto respondió con objeción directa o mensaje ambiguo |
| 010_complex_case.md | Complex | Múltiples señales contradictorias |

## Reglas

- No agregar conversaciones al dataset durante la Beta v1.0.
- No modificar conversaciones existentes.
- Para la Beta v1.1 o posteriores, crear un dataset nuevo en `beta_dataset_v1.1/`.

## Referencia

Ver `docs/beta_protocol.md` — Sección 2: Dataset congelado.
