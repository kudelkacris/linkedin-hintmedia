#!/usr/bin/env python3
"""
Corre DESPUÉS de que un humano completa la columna CORRECTO (SI/NO) en
outputs/manual_review_sample.csv. Calcula precisión real por bucket de confidence
y decide si recomendar RUN_FULL_BATCH.

Uso: python compute_precision.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

PRECISION_THRESHOLD = 0.85


def load_sample():
    path = os.path.join(config.OUTPUT_DIR, 'manual_review_sample.csv')
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def pct(n, total):
    return round(100 * n / total, 1) if total else None


def main():
    rows = load_sample()
    pending = [r for r in rows if not (r.get('CORRECTO') or '').strip()]
    if pending:
        print(f'ADVERTENCIA: {len(pending)}/{len(rows)} filas todavía no tienen CORRECTO completado.')
        print('La precisión se calcula solo sobre las filas ya revisadas. Completar manual_review_sample.csv')
        print('a mano (columna CORRECTO = SI o NO) antes de tomar la recomendación como definitiva.\n')

    by_bucket = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
    for r in rows:
        correcto = (r.get('CORRECTO') or '').strip().upper()
        if correcto not in ('SI', 'NO'):
            continue
        bucket = r['INFERENCE_CONFIDENCE'].strip().upper()
        if bucket in by_bucket:
            by_bucket[bucket].append(correcto == 'SI')

    results = {}
    for bucket, values in by_bucket.items():
        total = len(values)
        correct = sum(values)
        results[bucket] = {'total_revisado': total, 'correctos': correct, 'precision_pct': pct(correct, total)}

    applied_values = by_bucket['HIGH'] + by_bucket['MEDIUM']
    total_applied = len(applied_values)
    correct_applied = sum(applied_values)
    precision_applied_pct = pct(correct_applied, total_applied)

    run_full_batch = (precision_applied_pct is not None) and (precision_applied_pct >= PRECISION_THRESHOLD * 100)

    print('--- PRECISIÓN POR BUCKET ---')
    for bucket, r in results.items():
        print(f"{bucket}: {r['correctos']}/{r['total_revisado']} correctos "
              f"({r['precision_pct']}%)" if r['total_revisado'] else f'{bucket}: sin filas revisadas')

    print(f'\n--- PRECISION_APPLIED (HIGH + MEDIUM, lo único que toca el dataset) ---')
    if total_applied:
        print(f'{correct_applied}/{total_applied} correctos ({precision_applied_pct}%)')
    else:
        print('Sin filas HIGH/MEDIUM revisadas todavía.')

    print(f'\nUmbral configurado: {PRECISION_THRESHOLD*100:.0f}%')
    print(f'RUN_FULL_BATCH = {"TRUE" if run_full_batch else "FALSE"}')
    if not run_full_batch and total_applied:
        print('Recomendación: NO correr el batch completo todavía. Revisar el prompt/guardrails en los '
              'campos con más errores antes de reintentar.')
    elif run_full_batch:
        print('Recomendación: la precisión auditada supera el umbral. Se puede considerar correr '
              '`python enrichment_pipeline.py --limit 0` para los 137 candidatos completos.')

    out = {
        'umbral_precision': PRECISION_THRESHOLD,
        'por_bucket': results,
        'precision_applied_pct': precision_applied_pct,
        'total_applied_revisado': total_applied,
        'run_full_batch_recomendado': run_full_batch,
        'filas_pendientes_de_revision': len(pending),
    }
    out_path = os.path.join(config.OUTPUT_DIR, 'precision_result.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'\nResultado guardado en {out_path}')


if __name__ == '__main__':
    main()
