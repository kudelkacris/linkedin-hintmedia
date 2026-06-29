#!/usr/bin/env python3
"""
Orquestador del pipeline. Lee conversaciones/*.md, extrae y clasifica por
regex/heurísticas (sin IA), completa huecos críticos desde historial.json
cuando es posible, y escribe outputs/dataset.csv, dataset.json,
needs_ai_review.csv, stats.json y report.md.
"""
import csv
import json
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import extractors
import heuristics
import analytics


def load_historial():
    if not os.path.exists(config.HISTORIAL_PATH):
        return []
    with open(config.HISTORIAL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_historial_index(historial):
    """Índice por nombre normalizado para fallback de campos faltantes."""
    idx = {}
    for entry in historial:
        key = (entry.get('name') or '').strip().lower()
        if key:
            idx[key] = entry
    return idx


def fill_from_historial(record, raw, historial_idx):
    """Completa EMPRESA/PAIS/SECTOR/CARGO desde historial.json si el .md no los tenía."""
    key = (raw['nombre'] or '').strip().lower()
    entry = historial_idx.get(key)
    if not entry:
        return record
    if not record['EMPRESA'] and entry.get('empresa'):
        record['EMPRESA'] = entry['empresa']
    if not record['SECTOR'] and entry.get('sector'):
        record['SECTOR'] = entry['sector']
    if not record['CARGO'] and entry.get('tipoPerfil'):
        record['CARGO'] = entry.get('tipoPerfil', record['CARGO'])
    return record


def main():
    log = {'procesados': 0, 'errores': [], 'campos_vacios': {f: 0 for f in config.FIELDS}}

    historial = load_historial()
    historial_idx = build_historial_index(historial)

    md_paths = sorted(glob.glob(os.path.join(config.CONVERSACIONES_DIR, '*.md')))
    print(f'Archivos encontrados: {len(md_paths)}')

    records = []
    for i, path in enumerate(md_paths, start=1):
        fname = os.path.basename(path)
        try:
            raw = extractors.parse_file(path)
            conv_id = f'CONV_{i:04d}'
            record = heuristics.classify_record(raw, conv_id)
            record = fill_from_historial(record, raw, historial_idx)
            records.append(record)
            log['procesados'] += 1
            for f in config.FIELDS:
                if not record.get(f):
                    log['campos_vacios'][f] += 1
        except Exception as e:
            log['errores'].append({'archivo': fname, 'error': str(e)})
            print(f'  ERROR procesando {fname}: {e}')

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # dataset.csv / dataset.json
    csv_path = os.path.join(config.OUTPUT_DIR, 'dataset.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=config.FIELDS + ['NEEDS_AI'])
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, '') for k in config.FIELDS + ['NEEDS_AI']})

    json_path = os.path.join(config.OUTPUT_DIR, 'dataset.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # needs_ai_review.csv — solo registros con al menos un campo crítico vacío
    needs_ai_records = [r for r in records if r.get('NEEDS_AI')]
    needs_ai_path = os.path.join(config.OUTPUT_DIR, 'needs_ai_review.csv')
    with open(needs_ai_path, 'w', encoding='utf-8', newline='') as f:
        cols = ['ID_CONVERSACION', 'PROSPECTO', 'FUENTE_ARCHIVO'] + config.NEEDS_AI_FIELDS
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for r in needs_ai_records:
            writer.writerow({k: r.get(k, '') for k in cols})

    # stats.json + report.md
    stats = analytics.compute_stats(records)
    stats_path = os.path.join(config.OUTPUT_DIR, 'stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    report_md = analytics.build_report_md(stats, records)
    report_path = os.path.join(config.OUTPUT_DIR, 'report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    # log final
    print('\n--- RESUMEN ---')
    print(f"Procesados OK: {log['procesados']}/{len(md_paths)}")
    print(f"Errores: {len(log['errores'])}")
    for e in log['errores']:
        print(f"  - {e['archivo']}: {e['error']}")
    print(f"Necesitan revisión IA: {len(needs_ai_records)} ({analytics.pct(len(needs_ai_records), len(records))}%)")
    print('\nCampos más vacíos (top 8):')
    for field, n in sorted(log['campos_vacios'].items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {field}: {n} vacíos ({analytics.pct(n, len(records))}%)")
    print(f"\nOutputs escritos en: {config.OUTPUT_DIR}")
    print(f"  - dataset.csv / dataset.json ({len(records)} registros)")
    print(f"  - needs_ai_review.csv ({len(needs_ai_records)} registros)")
    print(f"  - stats.json / report.md")


if __name__ == '__main__':
    main()
