#!/usr/bin/env python3
"""
Lee historial.json (427 contactos del programa) y genera un reporte de conversión
completo sin usar la API. Usa las mismas reglas de sector/seniority que dataset_builder.

Output: dataset_builder/outputs/historial_report.md + historial_dataset.json
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import heuristics as h

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORIAL_PATH = os.path.join(BASE_DIR, 'historial.json')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')


STAGE_LABELS = {
    1: 'MSG1 generado',
    2: 'MSG2 / contacto inicial',
    3: 'Dossier enviado',
    4: 'Seguimiento (SEG1/2)',
    5: 'Avanzado / reunión',
}


def load_historial():
    with open(HISTORIAL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_variante(msg1_text):
    return h.detect_variante_msg1(msg1_text or '')


def respondio(conversation_history):
    """¿El prospecto mandó al menos un mensaje 'received'?"""
    return any(m.get('role') == 'received' for m in (conversation_history or []))


def count_respuestas(conversation_history):
    return sum(1 for m in (conversation_history or []) if m.get('role') == 'received')


def dossier_enviado(record):
    # stage 3+ = dossier enviado. extraMsgs tiene texto pre-generado para todos, no es señal fiable.
    return record.get('stage', 1) >= 3


def seg_enviado(record):
    return record.get('stage', 1) >= 4


def resultado_final(stage, respondio_flag, dossier_flag, seg_flag):
    if stage >= 5:
        return 'REUNION/AVANZADO'
    if seg_flag:
        return 'SEGUIMIENTO'
    if dossier_flag:
        return 'DOSSIER'
    if respondio_flag:
        return 'RESPONDIO_SIN_DOSSIER'
    return 'SIN_RESPUESTA'


def extract_cargo_from_profile(profile_raw):
    """profileRaw es texto libre de LinkedIn. La segunda línea no vacía suele ser el cargo."""
    lines = [l.strip() for l in (profile_raw or '').split('\n') if l.strip()]
    # skip name (primera línea), buscar primera línea que parezca cargo (no número, no símbolo)
    for line in lines[1:6]:
        if re.search(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}', line) and len(line) > 5:
            return line
    return ''


def pct(n, total):
    return round(100 * n / total, 1) if total else 0.0


def conversion_table(records, field, min_n=3):
    groups = {}
    for r in records:
        key = r.get(field) or '(sin dato)'
        groups.setdefault(key, {'total': 0, 'respondio': 0, 'dossier': 0, 'seg': 0, 'avanzado': 0})
        groups[key]['total'] += 1
        res = r['RESULTADO']
        if res != 'SIN_RESPUESTA':
            groups[key]['respondio'] += 1
        if res in ('DOSSIER', 'SEGUIMIENTO', 'REUNION/AVANZADO'):
            groups[key]['dossier'] += 1
        if res in ('SEGUIMIENTO', 'REUNION/AVANZADO'):
            groups[key]['seg'] += 1
        if res == 'REUNION/AVANZADO':
            groups[key]['avanzado'] += 1
    return {k: v for k, v in groups.items() if v['total'] >= min_n}


def main():
    data = load_historial()
    print(f'Cargados {len(data)} registros de historial.json')

    records = []
    for r in data:
        profile_raw = r.get('profileRaw', '')
        cargo = extract_cargo_from_profile(profile_raw)
        empresa = r.get('empresa', '')
        sector = h.detect_sector(empresa, cargo, profile_raw[:500])
        seniority = h.detect_seniority(cargo)
        variante = detect_variante(r.get('msg1', ''))
        ch = r.get('conversationHistory', [])
        resp = respondio(ch)
        n_resp = count_respuestas(ch)
        stage = r.get('stage', 1)
        dos = dossier_enviado(r)
        seg = seg_enviado(r)
        resultado = resultado_final(stage, resp, dos, seg)

        records.append({
            'ID': r.get('id', ''),
            'NOMBRE': r.get('name', ''),
            'EMPRESA': empresa,
            'CARGO': cargo,
            'SECTOR': sector,
            'SENIORITY': seniority,
            'VARIANTE': variante,
            'STAGE': stage,
            'STAGE_LABEL': STAGE_LABELS.get(stage, str(stage)),
            'RESPONDIO': 'SI' if resp else 'NO',
            'N_RESPUESTAS': n_resp,
            'DOSSIER_ENVIADO': 'SI' if dos else 'NO',
            'SEG_ENVIADO': 'SI' if seg else 'NO',
            'RESULTADO': resultado,
            'FECHA': r.get('date', ''),
        })

    # save json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, 'historial_dataset.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # ── build report ──────────────────────────────────────────────────────
    n = len(records)
    respondieron = sum(1 for r in records if r['RESPONDIO'] == 'SI')
    con_dossier = sum(1 for r in records if r['DOSSIER_ENVIADO'] == 'SI')
    con_seg = sum(1 for r in records if r['SEG_ENVIADO'] == 'SI')
    avanzados = sum(1 for r in records if r['RESULTADO'] == 'REUNION/AVANZADO')

    lines = [
        '# Reporte historial completo (427 contactos del programa)\n',
        f'Total contactos: **{n}**\n',
        '## Embudo general\n',
        '| Etapa | N | % del total |',
        '|---|---|---|',
        f'| Respondieron al menos 1 mensaje | {respondieron} | {pct(respondieron,n)}% |',
        f'| Llegaron a dossier | {con_dossier} | {pct(con_dossier,n)}% |',
        f'| Llegaron a seguimiento (SEG) | {con_seg} | {pct(con_seg,n)}% |',
        f'| Avanzado / reunión (stage 5) | {avanzados} | {pct(avanzados,n)}% |',
        '',
        '## Por stage\n',
        '| Stage | Label | N | % |',
        '|---|---|---|---|',
    ]
    stage_counts = Counter(r['STAGE'] for r in records)
    for s in sorted(stage_counts):
        cnt = stage_counts[s]
        lines.append(f'| {s} | {STAGE_LABELS.get(s, "?")} | {cnt} | {pct(cnt,n)}% |')
    lines.append('')

    # por sector
    lines.append('## Por sector (mín. 3 casos, excluye sin dato)\n')
    sec_data = conversion_table(records, 'SECTOR', min_n=3)
    sec_data = {k: v for k, v in sec_data.items() if k != '(sin dato)'}
    lines.append('| Sector | Total | % respondió | % dossier | % seg+ |')
    lines.append('|---|---|---|---|---|')
    for k, v in sorted(sec_data.items(), key=lambda kv: -kv[1]['dossier']):
        t = v['total']
        lines.append(f"| {k} | {t} | {pct(v['respondio'],t)}% | {pct(v['dossier'],t)}% | {pct(v['seg'],t)}% |")
    lines.append('')

    # por variante
    lines.append('## Por variante MSG1\n')
    var_data = conversion_table(records, 'VARIANTE', min_n=1)
    lines.append('| Variante | Total | % respondió | % dossier | % seg+ |')
    lines.append('|---|---|---|---|---|')
    for k, v in sorted(var_data.items(), key=lambda kv: -kv[1]['total']):
        t = v['total']
        lines.append(f"| {k} | {t} | {pct(v['respondio'],t)}% | {pct(v['dossier'],t)}% | {pct(v['seg'],t)}% |")
    lines.append('')

    # por seniority
    lines.append('## Por seniority (mín. 3 casos)\n')
    sen_data = conversion_table(records, 'SENIORITY', min_n=3)
    lines.append('| Seniority | Total | % respondió | % dossier | % seg+ |')
    lines.append('|---|---|---|---|---|')
    for k, v in sorted(sen_data.items(), key=lambda kv: -kv[1]['dossier']):
        t = v['total']
        lines.append(f"| {k} | {t} | {pct(v['respondio'],t)}% | {pct(v['dossier'],t)}% | {pct(v['seg'],t)}% |")
    lines.append('')

    lines.append('## Cobertura sector\n')
    sin_sector = sum(1 for r in records if not r['SECTOR'])
    lines.append(f'- Con sector detectado: **{n - sin_sector}** ({pct(n-sin_sector,n)}%)')
    lines.append(f'- Sin sector (empresa no reconocida): **{sin_sector}** ({pct(sin_sector,n)}%)')
    lines.append('')
    lines.append('_Sin API. Todo regex sobre historial.json._')

    out_path = os.path.join(OUTPUT_DIR, 'historial_report.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'Reporte: {out_path}')
    print(f'Dataset: {json_path}')
    print(f'\nResumen:')
    print(f'  Total: {n}')
    print(f'  Respondieron: {respondieron} ({pct(respondieron,n)}%)')
    print(f'  Dossier: {con_dossier} ({pct(con_dossier,n)}%)')
    print(f'  Seguimiento: {con_seg} ({pct(con_seg,n)}%)')
    print(f'  Avanzado: {avanzados} ({pct(avanzados,n)}%)')


if __name__ == '__main__':
    main()
