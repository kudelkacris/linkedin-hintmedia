#!/usr/bin/env python3
"""
Construye outputs/manual_review_sample.csv: muestra aleatoria de 10 HIGH + 10 MEDIUM + 10 LOW
sacada de la última corrida de enrichment_pipeline.py (enriched_dataset.csv + suggested_values.csv).
NO corre el pipeline de nuevo, NO toca el dataset. Solo prepara la auditoría humana.
"""
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

SAMPLE_PER_BUCKET = 10
RANDOM_SEED = 42  # fijo, para que la muestra sea reproducible si se vuelve a correr


def load_dataset_index():
    with open(config.DATASET_JSON, 'r', encoding='utf-8') as f:
        return {r['ID_CONVERSACION']: r for r in json.load(f)}


def load_enriched():
    path = os.path.join(config.OUTPUT_DIR, 'enriched_dataset.csv')
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_suggested():
    path = os.path.join(config.OUTPUT_DIR, 'suggested_values.csv')
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def to_audit_row(r, dataset_idx, value_key):
    record = dataset_idx.get(r['ID_CONVERSACION'], {})
    return {
        'ID_CONVERSACION': r['ID_CONVERSACION'],
        'PROSPECTO': r['PROSPECTO'],
        'CAMPO_ENRIQUECIDO': r['FIELD'],
        'VALOR_ORIGINAL': record.get(r['FIELD'], ''),  # casi siempre vacío por construcción (era el motivo de enriquecer)
        'VALOR_IA': r[value_key],
        'INFERENCE_CONFIDENCE': r['CONFIDENCE'],
        'EVIDENCE_USED': r['EVIDENCE'],
        'INFERENCE_REASON': r['REASON'],
        'REVISOR': '',
        'CORRECTO': '',
        'OBSERVACIONES': '',
    }


def main():
    random.seed(RANDOM_SEED)
    dataset_idx = load_dataset_index()
    enriched = load_enriched()
    suggested = load_suggested()

    high_pool = [r for r in enriched if r['CONFIDENCE'] == 'HIGH']
    medium_pool = [r for r in enriched if r['CONFIDENCE'] == 'MEDIUM']
    low_pool = [r for r in suggested if r['CONFIDENCE'] == 'LOW']

    pools = {'HIGH': (high_pool, 'VALUE'), 'MEDIUM': (medium_pool, 'VALUE'), 'LOW': (low_pool, 'SUGGESTED_VALUE')}

    sample_rows = []
    shortfalls = {}
    for bucket, (pool, value_key) in pools.items():
        n = min(SAMPLE_PER_BUCKET, len(pool))
        if n < SAMPLE_PER_BUCKET:
            shortfalls[bucket] = f'pool tiene {len(pool)}, se pidieron {SAMPLE_PER_BUCKET}'
        chosen = random.sample(pool, n)
        for r in chosen:
            sample_rows.append(to_audit_row(r, dataset_idx, value_key))

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    sample_path = os.path.join(config.OUTPUT_DIR, 'manual_review_sample.csv')
    cols = ['ID_CONVERSACION', 'PROSPECTO', 'CAMPO_ENRIQUECIDO', 'VALOR_ORIGINAL', 'VALOR_IA',
            'INFERENCE_CONFIDENCE', 'EVIDENCE_USED', 'INFERENCE_REASON', 'REVISOR', 'CORRECTO', 'OBSERVACIONES']
    with open(sample_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sample_rows)

    build_audit_report(high_pool, medium_pool, low_pool, sample_rows, shortfalls)

    print(f'Muestra escrita: {sample_path} ({len(sample_rows)} filas)')
    if shortfalls:
        print('ADVERTENCIA — pools insuficientes para 10/10/10:')
        for bucket, msg in shortfalls.items():
            print(f'  {bucket}: {msg}')
    print('Siguiente paso: completar a mano las columnas REVISOR/CORRECTO(SI o NO)/OBSERVACIONES,')
    print('después correr compute_precision.py sobre el CSV ya completado.')


def field_counts(pool, value_key='FIELD'):
    counts = {}
    for r in pool:
        counts[r['FIELD']] = counts.get(r['FIELD'], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def build_audit_report(high_pool, medium_pool, low_pool, sample_rows, shortfalls):
    lines = ['# Auditoría manual — Reporte previo a revisión humana\n']
    lines.append('Este reporte describe la MUESTRA preparada, no resultados de precisión todavía '
                  '(eso requiere que un humano complete `manual_review_sample.csv` primero).\n')

    lines.append('## Tamaño de los pools disponibles (corrida actual, limit=20)\n')
    lines.append('| Bucket | Disponibles | Muestreados |')
    lines.append('|---|---|---|')
    lines.append(f'| HIGH | {len(high_pool)} | {min(10, len(high_pool))} |')
    lines.append(f'| MEDIUM | {len(medium_pool)} | {min(10, len(medium_pool))} |')
    lines.append(f'| LOW | {len(low_pool)} | {min(10, len(low_pool))} |')
    lines.append('')

    if shortfalls:
        lines.append('## ⚠ Advertencia — pools insuficientes\n')
        for bucket, msg in shortfalls.items():
            lines.append(f'- **{bucket}**: {msg}. La muestra para este bucket no llega a 10 — '
                          f'la corrida actual fue solo sobre 20 conversaciones de prueba.')
        lines.append('')

    lines.append('## Campos enriquecidos por categoría\n')
    for label, pool in [('HIGH', high_pool), ('MEDIUM', medium_pool), ('LOW (suggested)', low_pool)]:
        lines.append(f'**{label}**:')
        for field, n in field_counts(pool).items():
            lines.append(f'- {field}: {n}')
        lines.append('')

    lines.append('## Estimación de riesgo (cualitativa, antes de revisión humana)\n')
    lines.append('- **HIGH**: riesgo bajo esperado — el guardrail de `confidence_engine.py` exige evidencia '
                  'no vacía y valor dentro del enum para llegar a HIGH. Riesgo residual: alucinación '
                  'semánticamente plausible que cita evidencia real pero la interpreta mal.')
    lines.append('- **MEDIUM**: riesgo medio — mismo guardrail estructural, pero el modelo ya se autoevalúa '
                  'con menos certeza. Es el bucket donde más vale la pena gastar atención humana.')
    lines.append('- **LOW**: no se aplica al dataset (va a `suggested_values.csv`), así que el riesgo de '
                  'contaminación es nulo — pero vale auditar si el modelo descarta correctamente (falsos '
                  'negativos: campos que sí tenían evidencia suficiente y quedaron en LOW por error de criterio).')
    lines.append('')

    lines.append('## Metodología propuesta para calcular PRECISION REAL\n')
    lines.append('Después de que un humano complete `CORRECTO` (SI/NO) en `manual_review_sample.csv` para las '
                  '30 filas, correr `compute_precision.py`, que calcula:\n')
    lines.append('- `PRECISION_HIGH` = correctos en HIGH / total revisado en HIGH')
    lines.append('- `PRECISION_MEDIUM` = correctos en MEDIUM / total revisado en MEDIUM')
    lines.append('- `PRECISION_LOW` = correctos en LOW / total revisado en LOW '
                  '(interpretado como "el modelo descartó bien" cuando CORRECTO=SI sobre un LOW '
                  'significa que el valor sugerido, aunque no aplicado, era razonable)')
    lines.append('- `PRECISION_APPLIED` = correctos en (HIGH ∪ MEDIUM) / total revisado en (HIGH ∪ MEDIUM) — '
                  '**esta es la métrica que importa para decidir si escalar**, porque HIGH y MEDIUM son los '
                  'únicos que tocan el dataset real.')
    lines.append('')
    lines.append('**Regla de decisión**: si `PRECISION_APPLIED >= 85%`, el script imprime y deja constancia '
                  'de `RUN_FULL_BATCH = TRUE` (recomendación, no ejecuta nada solo). Si no llega a 85%, '
                  'imprime `RUN_FULL_BATCH = FALSE` y debería ajustarse el prompt/guardrails antes de '
                  'reintentar, no correr el batch completo igual.')
    lines.append('')

    report_path = os.path.join(config.OUTPUT_DIR, 'audit_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
