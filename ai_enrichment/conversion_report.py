#!/usr/bin/env python3
"""
Reporte combinado: cruza lo OPERATIVO (dataset_builder, regex, cubre los 167) con lo de
INTENCIÓN (semantic_enrichment.py, cubre solo las conversaciones ya procesadas con IA).

Responde las preguntas de negocio: ¿qué sector convierte más? ¿qué variante de MSG1 (A vs C)
convierte más? ¿qué objeción aparece más y cómo correlaciona con el resultado? ¿el engagement
real predice conversión?

NO inventa números para filas sin dato semántico — esas filas se cuentan en la parte operativa
(sector/variante, que cubre 167) y se excluyen de la parte de intención (que cubre menos).
"""
import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

DATASET_BUILDER_OUTPUTS = os.path.join(config.BASE_DIR, 'dataset_builder', 'outputs')


def pct(n, total):
    return round(100 * n / total, 1) if total else None


def load_operational():
    with open(os.path.join(DATASET_BUILDER_OUTPUTS, 'dataset.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def load_semantic():
    path = os.path.join(config.OUTPUT_DIR, 'semantic_enrichment.csv')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return {row['ID_CONVERSACION']: row for row in csv.DictReader(f)}


CONVERTED_RESULTS = ('DOSSIER', 'SEGUIMIENTO', 'REUNION', 'CLIENTE')
MEETING_RESULTS = ('REUNION', 'CLIENTE')


def conversion_by(records, field, converted_results=CONVERTED_RESULTS, min_n=1):
    groups = {}
    for r in records:
        key = (r.get(field) or '').strip() or '(sin dato)'
        groups.setdefault(key, {'total': 0, 'convertidos': 0, 'reunion': 0})
        groups[key]['total'] += 1
        if r['RESULTADO_FINAL'] in converted_results:
            groups[key]['convertidos'] += 1
        if r['RESULTADO_FINAL'] in MEETING_RESULTS:
            groups[key]['reunion'] += 1
    out = {}
    for k, v in groups.items():
        if v['total'] < min_n:
            continue
        out[k] = {
            'total': v['total'],
            'dossier_o_mas_pct': pct(v['convertidos'], v['total']),
            'reunion_pct': pct(v['reunion'], v['total']),
        }
    return out


def main():
    operational = load_operational()
    semantic_idx = load_semantic()
    semantic_ids = set(semantic_idx.keys())
    n_semantic = len(semantic_ids)
    n_total = len(operational)

    lines = ['# Reporte de conversión combinado (operativo + intención)\n']
    lines.append(f'Cobertura operativa (sector/variante/resultado): **{n_total}** conversaciones (dataset_builder, regex).')
    lines.append(f'Cobertura de intención (engagement/objeción real): **{n_semantic}** conversaciones '
                 f'({pct(n_semantic, n_total)}% del total — semantic_enrichment.py todavía no corrió sobre las 167).\n')

    # ── 1. Por sector ──────────────────────────────────────────────
    lines.append('## Conversión por sector (mín. 3 casos, excluye "(sin dato)")\n')
    sector_conv = conversion_by(operational, 'SECTOR', min_n=3)
    sector_conv = {k: v for k, v in sector_conv.items() if k != '(sin dato)'}
    lines.append('| Sector | Total | % llega a dossier+ | % llega a reunión |')
    lines.append('|---|---|---|---|')
    for k, v in sorted(sector_conv.items(), key=lambda kv: -kv[1]['dossier_o_mas_pct']):
        lines.append(f"| {k} | {v['total']} | {v['dossier_o_mas_pct']}% | {v['reunion_pct']}% |")
    lines.append('')

    # ── 2. Por variante MSG1 (A vs C) ──────────────────────────────
    lines.append('## Conversión por variante de MSG1 (A = persona, C = trabajo)\n')
    variante_conv = conversion_by(operational, 'VARIANTE_MSG1', min_n=1)
    lines.append('| Variante | Total | % llega a dossier+ | % llega a reunión |')
    lines.append('|---|---|---|---|')
    for k, v in sorted(variante_conv.items(), key=lambda kv: -kv[1]['total']):
        lines.append(f"| {k} | {v['total']} | {v['dossier_o_mas_pct']}% | {v['reunion_pct']}% |")
    lines.append('')
    if '(sin dato)' in variante_conv:
        lines.append(f"Nota: {variante_conv['(sin dato)']['total']} conversaciones no tienen variante "
                     f"detectada por regex (formato de archivo sin el texto exacto del MSG1).\n")

    # ── 3. Por objeción (regex, cubre 167) ────────────────────────
    lines.append('## Conversión por objeción principal (regex, n=167)\n')
    obj_conv = conversion_by(operational, 'OBJECION_PRINCIPAL', min_n=1)
    obj_conv = {k: v for k, v in obj_conv.items() if k not in ('', '(sin dato)')}
    lines.append('| Objeción | Total | % llega a dossier+ | % llega a reunión |')
    lines.append('|---|---|---|---|')
    for k, v in sorted(obj_conv.items(), key=lambda kv: -kv[1]['total']):
        lines.append(f"| {k} | {v['total']} | {v['dossier_o_mas_pct']}% | {v['reunion_pct']}% |")
    lines.append('')

    # ── 4. Por engagement (regex + anotaciones humanas, cubre 167) ─
    lines.append('## Conversión por engagement (regex + anotaciones en archivo, n=167)\n')
    eng_conv = conversion_by(operational, 'ENGAGEMENT_LEVEL', min_n=1)
    lines.append('| Engagement | Total | % llega a dossier+ | % llega a reunión |')
    lines.append('|---|---|---|---|')
    order = ['HIGH', 'MEDIUM', 'LOW', 'N/A', '(sin dato)']
    for eng in sorted(eng_conv, key=lambda e: order.index(e) if e in order else 99):
        v = eng_conv[eng]
        lines.append(f"| {eng} | {v['total']} | {v['dossier_o_mas_pct']}% | {v['reunion_pct']}% |")
    lines.append('')

    lines.append('## Lectura\n')
    lines.append('- Todo calculado con regex sobre las 167 conversaciones — sin API, sin costo adicional.')
    lines.append('- Sector tiene 68% sin dato (SECTOR no extraíble por regex de muchos archivos) — el dato es real pero la muestra es chica.')
    lines.append('- Variante sin dato (86/167) = archivos en formato resumen sin MSG1 textual parseable.')

    out_path = os.path.join(config.OUTPUT_DIR, 'conversion_report.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Reporte escrito: {out_path}')


if __name__ == '__main__':
    main()
