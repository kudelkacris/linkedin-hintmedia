# Reporte de conversión combinado (operativo + intención)

Cobertura operativa (sector/variante/resultado): **167** conversaciones (dataset_builder, regex).
Cobertura de intención (engagement/objeción real): **167** conversaciones (100.0% del total — semantic_enrichment.py todavía no corrió sobre las 167).

## Conversión por sector (mín. 3 casos, excluye "(sin dato)")

| Sector | Total | % llega a dossier+ | % llega a reunión |
|---|---|---|---|
| Seguros/Finanzas | 4 | 100.0% | 0.0% |
| Tecnología | 9 | 66.7% | 0.0% |
| Educación | 3 | 66.7% | 0.0% |
| Turismo/Hotelería | 3 | 66.7% | 0.0% |
| Energía | 14 | 57.1% | 0.0% |
| Agencia/Marketing | 7 | 57.1% | 0.0% |
| Real Estate | 4 | 50.0% | 0.0% |
| Salud/Clínica | 4 | 50.0% | 0.0% |
| Retail/Consumo | 9 | 44.4% | 0.0% |
| Minería | 12 | 41.7% | 0.0% |
| Consultoría/Legal | 3 | 33.3% | 0.0% |
| Farmacéutico | 5 | 20.0% | 0.0% |
| Automotriz | 6 | 16.7% | 0.0% |

## Conversión por variante de MSG1 (A = persona, C = trabajo)

| Variante | Total | % llega a dossier+ | % llega a reunión |
|---|---|---|---|
| (sin dato) | 86 | 53.5% | 2.3% |
| A | 69 | 49.3% | 4.3% |
| C | 12 | 75.0% | 8.3% |

Nota: 86 conversaciones no tienen variante detectada por regex (formato de archivo sin el texto exacto del MSG1).

## Conversión por objeción principal (regex, n=167)

| Objeción | Total | % llega a dossier+ | % llega a reunión |
|---|---|---|---|
| NONE | 140 | 50.7% | 1.4% |
| PARTNERSHIP | 10 | 70.0% | 10.0% |
| BAD_TIMING | 5 | 60.0% | 0.0% |
| CURIOSITY_ONLY | 5 | 100.0% | 60.0% |
| HAS_AGENCY | 4 | 50.0% | 0.0% |
| NO_BUDGET | 1 | 100.0% | 0.0% |

## Conversión por engagement (regex + anotaciones en archivo, n=167)

| Engagement | Total | % llega a dossier+ | % llega a reunión |
|---|---|---|---|
| HIGH | 13 | 100.0% | 15.4% |
| MEDIUM | 51 | 82.4% | 2.0% |
| LOW | 56 | 39.3% | 5.4% |
| N/A | 47 | 25.5% | 0.0% |

## Lectura

- Todo calculado con regex sobre las 167 conversaciones — sin API, sin costo adicional.
- Sector tiene 68% sin dato (SECTOR no extraíble por regex de muchos archivos) — el dato es real pero la muestra es chica.
- Variante sin dato (86/167) = archivos en formato resumen sin MSG1 textual parseable.