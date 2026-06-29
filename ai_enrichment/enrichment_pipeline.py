#!/usr/bin/env python3
"""
Orquestador del enrichment. Lee needs_ai_review.csv (lista de conversaciones candidatas),
junta el contexto real (dataset.json + el .md original) por fila, llama una vez a Claude
por conversación pidiendo SOLO los campos vacíos, valida con guardrails, y separa el
resultado en enriched_dataset.csv (HIGH/MEDIUM aplicado) y suggested_values.csv (LOW, no aplicado).

NO modifica dataset_builder ni regenera el dataset original. Es un paso posterior, opcional.
"""
import argparse
import csv
import json
import os
import re
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import enrichment_prompts
import enrichment_validator


def load_api_key():
    if not os.path.exists(config.ENV_LOCAL):
        raise RuntimeError(f'No se encontró {config.ENV_LOCAL}')
    with open(config.ENV_LOCAL, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('ANTHROPIC_API_KEY='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('ANTHROPIC_API_KEY no está en .env.local')


def load_dataset_index():
    with open(config.DATASET_JSON, 'r', encoding='utf-8') as f:
        records = json.load(f)
    return {r['ID_CONVERSACION']: r for r in records}


def load_needs_ai_rows():
    with open(config.NEEDS_AI_CSV, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_raw_conversation(fuente_archivo):
    path = os.path.join(config.CONVERSACIONES_DIR, fuente_archivo)
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def fields_missing(record):
    """Igual que TARGET_FIELDS, pero MOTIVO_EXITO solo aplica si RESULTADO_FINAL es CLIENTE/REUNION,
    y MOTIVO_FRACASO solo si es SIN_RESPUESTA — mismo criterio que dataset_builder/heuristics.py,
    para no pedirle a la IA un "motivo de éxito" en una conversación que no fue ni éxito ni fracaso."""
    resultado = (record.get('RESULTADO_FINAL') or '').strip()
    missing = []
    for f in config.TARGET_FIELDS:
        if (record.get(f) or '').strip():
            continue
        if f == 'MOTIVO_EXITO' and resultado not in ('CLIENTE', 'REUNION'):
            continue
        if f == 'MOTIVO_FRACASO' and resultado != 'SIN_RESPUESTA':
            continue
        missing.append(f)
    return missing


def call_claude(client, api_key, system, prompt):
    payload = {
        'model': config.MODEL,
        'max_tokens': 1200,
        'messages': [{'role': 'user', 'content': prompt}],
        'system': system,
    }
    resp = client.post(
        config.API_URL, json=payload,
        headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['content'][0]['text']


def parse_response(text, fields):
    """Parsea <CAMPO>: / <CAMPO>_CONFIDENCE: / <CAMPO>_EVIDENCE: / <CAMPO>_REASON: por cada campo pedido."""
    out = {}
    for field in fields:
        def get(suffix=''):
            key = field + suffix
            # [ \t]* (no \s*) — \s también matchea \n, y si el valor queda vacío eso desplaza
            # la captura a la línea siguiente completa (bug real detectado en testing).
            m = re.search(r'^' + re.escape(key) + r':[ \t]*(.*)$', text, re.IGNORECASE | re.MULTILINE)
            return m.group(1).strip() if m else ''
        out[field] = {
            'value': get(''),
            'confidence': get('_CONFIDENCE'),
            'evidence': get('_EVIDENCE'),
            'reason': get('_REASON'),
        }
    return out


def process_record(client, api_key, needs_ai_row, record):
    fields = fields_missing(record)
    if not fields:
        return None, {}

    raw_text = load_raw_conversation(needs_ai_row['FUENTE_ARCHIVO'])
    if not raw_text:
        return None, {}

    prompt = enrichment_prompts.build_user_prompt(record, raw_text, fields)
    raw_response = call_claude(client, api_key, enrichment_prompts.SYSTEM, prompt)
    parsed = parse_response(raw_response, fields)

    field_results = {}
    for field in fields:
        p = parsed[field]
        field_results[field] = enrichment_validator.validate_field_result(
            field, p['value'], p['confidence'], p['evidence'], p['reason']
        )
    applied, suggested = enrichment_validator.validate_record_results(field_results)
    return raw_response, (applied, suggested)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=config.DEFAULT_TEST_LIMIT,
                         help='Cantidad de registros a procesar (default: 20, modo prueba). Usar 0 para todos.')
    args = parser.parse_args()

    api_key = load_api_key()
    dataset_idx = load_dataset_index()
    needs_ai_rows = load_needs_ai_rows()

    if args.limit > 0:
        needs_ai_rows = needs_ai_rows[:args.limit]

    print(f'Procesando {len(needs_ai_rows)} registros (de {len(load_needs_ai_rows())} candidatos totales en needs_ai_review.csv)')

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    enriched_rows = []   # ID_CONVERSACION, FIELD, VALUE, CONFIDENCE, EVIDENCE, REASON
    suggested_rows = []  # idem pero no aplicado
    errors = []
    confidences_seen = []

    with httpx.Client() as client:
        for i, row in enumerate(needs_ai_rows, start=1):
            conv_id = row['ID_CONVERSACION']
            record = dataset_idx.get(conv_id)
            if not record:
                errors.append({'id': conv_id, 'error': 'no encontrado en dataset.json'})
                continue
            try:
                print(f'[{i}/{len(needs_ai_rows)}] {row["PROSPECTO"]} ({conv_id})...')
                _, result = process_record(client, api_key, row, record)
                if result is None:
                    continue
                applied, suggested = result
                for field, r in applied.items():
                    enriched_rows.append({
                        'ID_CONVERSACION': conv_id, 'PROSPECTO': row['PROSPECTO'], 'FIELD': field,
                        'VALUE': r['value'], 'CONFIDENCE': r['confidence'], 'EVIDENCE': r['evidence'],
                        'REASON': r['reason'],
                    })
                    confidences_seen.append(r['confidence'])
                for field, r in suggested.items():
                    suggested_rows.append({
                        'ID_CONVERSACION': conv_id, 'PROSPECTO': row['PROSPECTO'], 'FIELD': field,
                        'SUGGESTED_VALUE': r['value'], 'CONFIDENCE': r['confidence'], 'EVIDENCE': r['evidence'],
                        'REASON': r['reason'], 'GUARDRAIL_NOTES': ' | '.join(r['guardrail_notes']),
                    })
                    confidences_seen.append(r['confidence'])
            except Exception as e:
                errors.append({'id': conv_id, 'error': str(e)})
                print(f'  ERROR: {e}')
            time.sleep(0.2)

    # ─── outputs ──────────────────────────────────────────────────────
    enriched_path = os.path.join(config.OUTPUT_DIR, 'enriched_dataset.csv')
    with open(enriched_path, 'w', encoding='utf-8', newline='') as f:
        cols = ['ID_CONVERSACION', 'PROSPECTO', 'FIELD', 'VALUE', 'CONFIDENCE', 'EVIDENCE', 'REASON']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(enriched_rows)

    suggested_path = os.path.join(config.OUTPUT_DIR, 'suggested_values.csv')
    with open(suggested_path, 'w', encoding='utf-8', newline='') as f:
        cols = ['ID_CONVERSACION', 'PROSPECTO', 'FIELD', 'SUGGESTED_VALUE', 'CONFIDENCE', 'EVIDENCE', 'REASON', 'GUARDRAIL_NOTES']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(suggested_rows)

    conf_counts = {c: confidences_seen.count(c) for c in config.CONFIDENCE_LEVELS}
    field_counts = {}
    for r in enriched_rows:
        field_counts[r['FIELD']] = field_counts.get(r['FIELD'], 0) + 1

    stats = {
        'registros_procesados': len(needs_ai_rows) - len(errors),
        'errores': len(errors),
        'campos_completados_aplicados': len(enriched_rows),
        'campos_solo_sugeridos': len(suggested_rows),
        'confidence_counts': conf_counts,
        'campos_mas_enriquecidos': dict(sorted(field_counts.items(), key=lambda kv: -kv[1])),
        'detalle_errores': errors,
    }
    stats_path = os.path.join(config.OUTPUT_DIR, 'enrichment_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    build_report(stats, needs_ai_rows, dataset_idx)

    print('\n--- RESUMEN ---')
    print(f"Procesados: {stats['registros_procesados']} | Errores: {stats['errores']}")
    print(f"Campos aplicados (HIGH/MEDIUM): {stats['campos_completados_aplicados']}")
    print(f"Campos solo sugeridos (LOW): {stats['campos_solo_sugeridos']}")
    print(f"Confidence: {conf_counts}")
    print(f"Outputs en: {config.OUTPUT_DIR}")


def build_report(stats, needs_ai_rows, dataset_idx):
    cobertura_antes = {}
    for f in config.TARGET_FIELDS:
        vacios = sum(1 for r in dataset_idx.values() if not (r.get(f) or '').strip())
        cobertura_antes[f] = vacios

    lines = ['# AI Enrichment — Reporte V1\n']
    lines.append(f"Registros procesados en esta corrida: **{stats['registros_procesados']}**")
    lines.append(f"Errores: **{stats['errores']}**\n")

    lines.append('## Cobertura antes (vacíos sobre todo el dataset, 167 registros)\n')
    lines.append('| Campo | Vacíos antes |')
    lines.append('|---|---|')
    for f, n in cobertura_antes.items():
        lines.append(f'| {f} | {n} |')
    lines.append('')

    lines.append('## Campos completados en esta corrida (aplicados a enriched_dataset.csv)\n')
    lines.append('| Campo | Completados (HIGH/MEDIUM) |')
    lines.append('|---|---|')
    for f, n in stats['campos_mas_enriquecidos'].items():
        lines.append(f'| {f} | {n} |')
    lines.append('')

    lines.append('## Distribución de confianza\n')
    lines.append('| Confidence | Cantidad |')
    lines.append('|---|---|')
    for c, n in stats['confidence_counts'].items():
        lines.append(f'| {c} | {n} |')
    lines.append('')

    lines.append(f"## Campos imposibles de inferir en esta corrida\n")
    lines.append(f"{stats['campos_solo_sugeridos']} valores quedaron en `suggested_values.csv` "
                  "(confidence LOW o sin evidencia) — no se aplicaron al dataset para no contaminarlo.\n")

    report_path = os.path.join(config.OUTPUT_DIR, 'enrichment_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
