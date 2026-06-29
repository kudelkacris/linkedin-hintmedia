#!/usr/bin/env python3
"""
Capa de verificación: cruza PIDIO_DOSSIER/DOSSIER_ENVIADO calculados por regex en
dataset_builder contra una extracción por IA más estricta (prompt del usuario, JSON,
NULL explícito, ignora mensajes del agente, respeta timing del funnel MSG1->MSG2 CTA->MSG3 dossier).

NO sobrescribe el dataset. Solo reporta acuerdos/desacuerdos para revisión humana,
mismo principio que ai_enrichment/enrichment_pipeline.py: nunca aplicar IA sin verificar.

Uso: python dossier_verification.py --limit 20
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
import dossier_verification_prompt as vp


def load_api_key():
    with open(config.ENV_LOCAL, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('ANTHROPIC_API_KEY='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('ANTHROPIC_API_KEY no está en .env.local')


def load_dataset():
    with open(config.DATASET_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_raw_conversation(fuente_archivo):
    path = os.path.join(config.CONVERSACIONES_DIR, fuente_archivo)
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def call_claude(client, api_key, system, prompt):
    payload = {
        'model': config.MODEL,
        'max_tokens': 800,
        'messages': [{'role': 'user', 'content': prompt}],
        'system': system,
    }
    resp = client.post(
        config.API_URL, json=payload,
        headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()['content'][0]['text']


def parse_json_response(text):
    """El modelo puede envolver el JSON en ```json ... ``` a pesar de la instrucción. Extraer el
    primer bloque {...} balanceado y parsearlo."""
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.MULTILINE).strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No se encontró JSON en la respuesta: {text[:200]}')
    return json.loads(cleaned[start:end + 1])


def to_si_no_null(value):
    v = (value or '').strip().upper()
    return {'TRUE': 'SI', 'FALSE': 'NO', 'NULL': ''}.get(v, '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()

    api_key = load_api_key()
    records = load_dataset()
    if args.limit > 0:
        records = records[:args.limit]

    print(f'Verificando {len(records)} conversaciones...')
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    rows = []
    errors = []
    with httpx.Client() as client:
        for i, r in enumerate(records, start=1):
            print(f'[{i}/{len(records)}] {r["PROSPECTO"]}...')
            raw_text = load_raw_conversation(r['FUENTE_ARCHIVO'])
            if not raw_text:
                continue
            try:
                prompt = vp.build_user_prompt(raw_text)
                raw_response = call_claude(client, api_key, vp.SYSTEM, prompt)
                parsed = parse_json_response(raw_response)

                ai_pidio = to_si_no_null(parsed.get('PIDIO_DOSSIER'))
                ai_enviado = to_si_no_null(parsed.get('DOSSIER_ENVIADO'))
                evidence = parsed.get('EVIDENCE', {}) or {}
                confidence = parsed.get('CONFIDENCE', {}) or {}

                regex_pidio = r.get('PIDIO_DOSSIER', '')
                regex_enviado = r.get('DOSSIER_ENVIADO', '')

                rows.append({
                    'ID_CONVERSACION': r['ID_CONVERSACION'],
                    'PROSPECTO': r['PROSPECTO'],
                    'FUENTE_ARCHIVO': r['FUENTE_ARCHIVO'],
                    'REGEX_PIDIO_DOSSIER': regex_pidio,
                    'AI_PIDIO_DOSSIER': ai_pidio if ai_pidio else 'NULL',
                    'AI_CONF_PIDIO': confidence.get('PIDIO_DOSSIER', ''),
                    'MATCH_PIDIO': 'SI' if (ai_pidio == regex_pidio or ai_pidio == '') else 'NO',
                    'REGEX_DOSSIER_ENVIADO': regex_enviado,
                    'AI_DOSSIER_ENVIADO': ai_enviado if ai_enviado else 'NULL',
                    'MATCH_ENVIADO': 'SI' if (ai_enviado == regex_enviado or ai_enviado == '') else 'NO',
                    'AI_DECISION_ROLE': parsed.get('DECISION_ROLE', ''),
                    'AI_CONF_DECISION_ROLE': confidence.get('DECISION_ROLE', ''),
                    'AI_EVIDENCE_PIDIO': evidence.get('PIDIO_DOSSIER', ''),
                    'AI_EVIDENCE_DECISION': evidence.get('DECISION_ROLE', ''),
                    'AI_REASONING': parsed.get('REASONING_SHORT', ''),
                })
            except Exception as e:
                errors.append({'id': r['ID_CONVERSACION'], 'prospecto': r['PROSPECTO'], 'error': str(e)})
                print(f'  ERROR: {e}')
            time.sleep(0.2)

    out_path = os.path.join(config.OUTPUT_DIR, 'dossier_verification.csv')
    cols = ['ID_CONVERSACION', 'PROSPECTO', 'FUENTE_ARCHIVO', 'REGEX_PIDIO_DOSSIER', 'AI_PIDIO_DOSSIER',
            'AI_CONF_PIDIO', 'MATCH_PIDIO', 'REGEX_DOSSIER_ENVIADO', 'AI_DOSSIER_ENVIADO', 'MATCH_ENVIADO',
            'AI_DECISION_ROLE', 'AI_CONF_DECISION_ROLE', 'AI_EVIDENCE_PIDIO', 'AI_EVIDENCE_DECISION', 'AI_REASONING']
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    disagree_pidio = [r for r in rows if r['MATCH_PIDIO'] == 'NO']
    disagree_enviado = [r for r in rows if r['MATCH_ENVIADO'] == 'NO']

    print('\n--- RESUMEN ---')
    print(f'Procesados: {len(rows)} | Errores: {len(errors)}')
    print(f'Desacuerdos PIDIO_DOSSIER (regex vs IA): {len(disagree_pidio)}/{len(rows)}')
    print(f'Desacuerdos DOSSIER_ENVIADO (regex vs IA): {len(disagree_enviado)}/{len(rows)}')
    if disagree_pidio or disagree_enviado:
        print('\nCasos en desacuerdo (revisar a mano antes de decidir cuál fuente confiar):')
        for r in disagree_pidio + disagree_enviado:
            if r not in []:
                print(f"  - {r['PROSPECTO']} ({r['FUENTE_ARCHIVO']}): regex_pidio={r['REGEX_PIDIO_DOSSIER']} "
                      f"ai_pidio={r['AI_PIDIO_DOSSIER']} | regex_enviado={r['REGEX_DOSSIER_ENVIADO']} "
                      f"ai_enviado={r['AI_DOSSIER_ENVIADO']}")
    print(f'\nOutput: {out_path}')


if __name__ == '__main__':
    main()
