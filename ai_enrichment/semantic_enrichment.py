#!/usr/bin/env python3
"""
Enriquecimiento semántico con separación dura entre estado operativo (CRM_STATE, calculado por
dataset_builder vía regex — verdad fija, la IA NUNCA lo toca) y señales semánticas (intención,
engagement, objeciones, citas textuales — eso sí lo extrae la IA del texto).

Distinto de enrichment_pipeline.py: ese completa campos vacíos (TIPO_PERFIL/SECTOR/AREA/etc).
Este SOLO genera una capa de intención/objeción más rica, sin tocar ni un campo operativo.

Uso: python semantic_enrichment.py --limit 20
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
import semantic_enrichment_prompt as sp


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


def build_crm_state(record):
    """Mapea los campos operativos YA calculados por dataset_builder (regex, verdad fija) al
    formato CRM_STATE que pide el prompt. Esto es lo único que cuenta como 'verdad' para la IA."""
    follow_up_count = (1 if record.get('SEG1_ENVIADO') == 'SI' else 0) + \
                       (1 if record.get('SEG2_ENVIADO') == 'SI' else 0)
    return {
        'dossier_sent': record.get('DOSSIER_ENVIADO') == 'SI',
        'follow_up_count': follow_up_count,
        'call_scheduled': record.get('CALL_AGENDADA') == 'SI',
        'pipeline_status': record.get('RESULTADO_FINAL', ''),
    }


def call_claude(client, api_key, system, prompt):
    payload = {
        'model': config.MODEL,
        'max_tokens': 900,
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


def repair_json(text):
    """Reparos heurísticos comunes en JSON generado por LLM: comas finales antes de } o ],
    comillas tipográficas en vez de rectas. No intenta arreglar nada más agresivo — si esto no
    alcanza, se deja fallar (mejor un error visible que un parche que esconda datos corruptos)."""
    repaired = text
    repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)  # trailing comma
    repaired = repaired.replace('“', '"').replace('”', '"').replace('’', "'")
    return repaired


def parse_json_response(text):
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.MULTILINE).strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No se encontró JSON en la respuesta: {text[:200]}')
    candidate = cleaned[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return json.loads(repair_json(candidate))  # si esto también falla, se propaga el error


def crm_state_was_respected(sent_crm_state, echoed_operational_state):
    """Guardrail: el modelo debe devolver CRM_STATE exactamente igual a como se lo mandamos.
    Si lo alteró, es una violación de la regla central del prompt — la fila se marca y no se confía
    en ninguno de sus otros campos tampoco (si no respeta esto, no hay garantía de que respetó el resto)."""
    if not isinstance(echoed_operational_state, dict):
        return False
    return all(sent_crm_state.get(k) == echoed_operational_state.get(k) for k in sent_crm_state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()

    api_key = load_api_key()
    records = load_dataset()
    if args.limit > 0:
        records = records[:args.limit]

    print(f'Procesando {len(records)} conversaciones...')
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    rows = []
    violations = []
    errors = []

    with httpx.Client() as client:
        for i, r in enumerate(records, start=1):
            print(f'[{i}/{len(records)}] {r["PROSPECTO"]}...')
            raw_text = load_raw_conversation(r['FUENTE_ARCHIVO'])
            if not raw_text:
                continue
            crm_state = build_crm_state(r)
            try:
                prompt = sp.build_user_prompt(crm_state, raw_text)
                parsed = None
                last_err = None
                for attempt in range(2):  # 1 intento + 1 reintento si el JSON sale malformado
                    raw_response = call_claude(client, api_key, sp.SYSTEM, prompt)
                    try:
                        parsed = parse_json_response(raw_response)
                        break
                    except (json.JSONDecodeError, ValueError) as e:
                        last_err = e
                        if attempt == 0:
                            print(f'  JSON malformado, reintentando...')
                if parsed is None:
                    raise last_err

                respected = crm_state_was_respected(crm_state, parsed.get('OPERATIONAL_STATE'))
                if not respected:
                    violations.append({'id': r['ID_CONVERSACION'], 'prospecto': r['PROSPECTO'],
                                        'crm_state_enviado': crm_state,
                                        'operational_state_devuelto': parsed.get('OPERATIONAL_STATE')})
                    print(f'  ⚠ VIOLACIÓN: el modelo alteró CRM_STATE, fila descartada')
                    continue

                intent = parsed.get('INTENT', {}) or {}
                confidence = parsed.get('CONFIDENCE', {}) or {}
                rows.append({
                    'ID_CONVERSACION': r['ID_CONVERSACION'],
                    'PROSPECTO': r['PROSPECTO'],
                    'CRM_dossier_sent': crm_state['dossier_sent'],
                    'CRM_follow_up_count': crm_state['follow_up_count'],
                    'CRM_call_scheduled': crm_state['call_scheduled'],
                    'CRM_pipeline_status': crm_state['pipeline_status'],
                    'INTEREST_LEVEL': intent.get('interest_level', ''),
                    'ENGAGEMENT': intent.get('engagement', ''),
                    'RESPONSE_QUALITY': intent.get('response_quality', ''),
                    'OBJECTIONS': ' | '.join(parsed.get('OBJECTIONS', []) or []),
                    'KEY_SIGNALS': ' | '.join(parsed.get('KEY_SIGNALS', []) or []),
                    'SUMMARY': parsed.get('CONVERSATION_SUMMARY', ''),
                    'CONF_INTENT': confidence.get('intent', ''),
                    'CONF_SIGNALS': confidence.get('signals', ''),
                })
            except Exception as e:
                errors.append({'id': r['ID_CONVERSACION'], 'prospecto': r['PROSPECTO'], 'error': str(e)})
                print(f'  ERROR: {e}')
            time.sleep(0.2)

    out_path = os.path.join(config.OUTPUT_DIR, 'semantic_enrichment.csv')
    cols = ['ID_CONVERSACION', 'PROSPECTO', 'CRM_dossier_sent', 'CRM_follow_up_count', 'CRM_call_scheduled',
            'CRM_pipeline_status', 'INTEREST_LEVEL', 'ENGAGEMENT', 'RESPONSE_QUALITY', 'OBJECTIONS',
            'KEY_SIGNALS', 'SUMMARY', 'CONF_INTENT', 'CONF_SIGNALS']
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    violations_path = os.path.join(config.OUTPUT_DIR, 'semantic_enrichment_violations.json')
    with open(violations_path, 'w', encoding='utf-8') as f:
        json.dump(violations, f, ensure_ascii=False, indent=2)

    print('\n--- RESUMEN ---')
    print(f'Procesados OK: {len(rows)} | Violaciones de CRM_STATE: {len(violations)} | Errores: {len(errors)}')
    print(f'Output: {out_path}')
    if violations:
        print(f'Violaciones guardadas en: {violations_path} (revisar — el modelo no debería alterar CRM_STATE nunca)')


if __name__ == '__main__':
    main()
