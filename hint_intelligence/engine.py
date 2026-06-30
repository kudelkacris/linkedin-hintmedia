#!/usr/bin/env python3
"""
Hint Intelligence Engine — engine.py
Orquestador principal de la Fase 1: Observación.

Uso:
    python hint_intelligence/engine.py           # corrida completa
    python hint_intelligence/engine.py --report  # solo regenera el reporte
    python hint_intelligence/engine.py --context # solo regenera context_injection.json
"""
import argparse
import json
import os
import sys
import traceback
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import pattern_engine
import knowledge_base
import change_detector
import report_builder


def log(msg):
    print(f'[HIE {datetime.now().strftime("%H:%M:%S")}] {msg}')


def save_engine_log(entry):
    log_path = config.OUT_LOG
    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    existing = []
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    existing.append(entry)
    existing = existing[-50:]  # solo últimas 50 corridas
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def run_full():
    start = datetime.now()
    log_entry = {
        'timestamp': start.isoformat(),
        'fase': 1,
        'status': 'OK',
        'n_historial': 0,
        'n_dataset_md': 0,
        'n_insights': 0,
        'n_sectores': 0,
        'errores': [],
    }

    # ── 1. Verificar fuentes de datos ────────────────────────────────────────
    if not os.path.exists(config.HISTORIAL_DATASET):
        log_entry['status'] = 'ERROR'
        log_entry['errores'].append(f'No existe {config.HISTORIAL_DATASET}')
        log_entry['errores'].append('Correr: python dataset_builder/historial_report.py')
        save_engine_log(log_entry)
        print('\n[HIE] ERROR: Ejecutá primero:')
        print('  python dataset_builder/historial_report.py')
        return False

    # ── 2. Cargar datos ───────────────────────────────────────────────────────
    log('Cargando fuentes de datos...')
    records_hist = pattern_engine.load_historial_dataset()
    records_ds   = pattern_engine.load_dataset_json()
    log(f'  historial_dataset: {len(records_hist)} registros')
    log(f'  dataset (/.md):    {len(records_ds)} registros')
    log_entry['n_historial'] = len(records_hist)
    log_entry['n_dataset_md'] = len(records_ds)

    # ── 3. Pattern engine ─────────────────────────────────────────────────────
    log('Ejecutando pattern_engine...')
    patterns = pattern_engine.run(records_hist, records_ds)
    n_insights = len(patterns.get('insights', []))
    log(f'  Sectores: {len(patterns["por_sector"])} | Insights: {n_insights}')
    log_entry['n_insights'] = n_insights
    log_entry['n_sectores'] = len(patterns['por_sector'])

    # ── 4. Change detection (antes de sobreescribir KB) ──────────────────────
    log('Detectando cambios respecto a corrida anterior...')
    import json as _json
    patterns_old = {}
    if os.path.exists(config.KB_PATTERNS):
        with open(config.KB_PATTERNS, 'r', encoding='utf-8') as _f:
            patterns_old = _json.load(_f)
    alerts = change_detector.run(patterns, patterns_old)
    change_detector.save_alerts(alerts)
    if alerts:
        log(f'  {len(alerts)} alerta(s) detectada(s):')
        for a in alerts:
            sev = a.get("severidad", "?")
            log(f'    [{sev}] {a["titulo"]}')
    else:
        log('  Sin cambios relevantes respecto a corrida anterior.')
    log_entry['n_alertas'] = len(alerts)

    # ── 5. Knowledge base ─────────────────────────────────────────────────────
    log('Actualizando knowledge_base...')
    knowledge_base.save_patterns(patterns)
    sectors    = knowledge_base.build_sector_intelligence(patterns)
    objections = knowledge_base.build_objection_playbook(patterns)
    log(f'  KB actualizada — {len(sectors)} sectores, {len(objections)} objeciones')

    # ── 6. Context injection ──────────────────────────────────────────────────
    log('Generando context_injection.json...')
    knowledge_base.build_context_injection(sectors, patterns)

    # ── 7. Reporte ────────────────────────────────────────────────────────────
    log('Generando intelligence_report.md...')
    report_path = report_builder.build(patterns, sectors, objections, alerts)
    log(f'  Reporte: {report_path}')

    # ── 8. Log ────────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start).total_seconds()
    log_entry['elapsed_s'] = round(elapsed, 2)
    save_engine_log(log_entry)

    # ── Resumen ───────────────────────────────────────────────────────────────
    g = patterns['global']
    print()
    print('=' * 60)
    print('  HINT INTELLIGENCE ENGINE - Fase 1 completada')
    print('=' * 60)
    print(f'  Contactos analizados : {g.get("n", 0)}')
    print(f'  Dossier rate global  : {g.get("dossier_pct", 0)}%')
    print(f'  Sectores detectados  : {len(sectors)}')
    print(f'  Insights generados   : {n_insights}')
    print(f'  Tiempo               : {elapsed:.1f}s')
    print()
    print('  Outputs:')
    print(f'    {config.KB_PATTERNS}')
    print(f'    {config.KB_SECTORS}')
    print(f'    {config.OUT_CONTEXT}')
    print(f'    {config.OUT_REPORT}')
    print()

    # Imprimir insights destacados
    for ins in patterns.get('insights', []):
        icon = {'CONVERSION_PATTERN': '[PATRON]', 'WARNING': '[ALERTA]',
                 'TARGETING_WARNING': '[TARGET]', 'EXPERIMENT_NEEDED': '[TEST]'}.get(ins['tipo'], '[INFO]')
        titulo = ins["titulo"].encode('ascii', 'replace').decode('ascii')
        print(f'  {icon} {titulo}')

    print()
    return True


def run_context_only():
    """Regenera solo el context_injection.json desde la KB existente."""
    if not os.path.exists(config.KB_PATTERNS):
        print('[HIE] KB no existe. Correr primero: python hint_intelligence/engine.py')
        return False
    import json
    with open(config.KB_PATTERNS, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    with open(config.KB_SECTORS, 'r', encoding='utf-8') as f:
        sectors = json.load(f)
    knowledge_base.build_context_injection(sectors, patterns)
    log(f'context_injection.json actualizado → {config.OUT_CONTEXT}')
    return True


def run_report_only():
    """Regenera solo el reporte desde la KB existente."""
    if not os.path.exists(config.KB_PATTERNS):
        print('[HIE] KB no existe. Correr primero: python hint_intelligence/engine.py')
        return False
    import json
    with open(config.KB_PATTERNS, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    with open(config.KB_SECTORS, 'r', encoding='utf-8') as f:
        sectors = json.load(f)
    with open(config.KB_OBJECTIONS, 'r', encoding='utf-8') as f:
        objections = json.load(f)
    report_path = report_builder.build(patterns, sectors, objections)
    log(f'Reporte regenerado → {report_path}')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hint Intelligence Engine — Fase 1')
    parser.add_argument('--report',  action='store_true', help='Solo regenerar el reporte desde KB existente')
    parser.add_argument('--context', action='store_true', help='Solo regenerar context_injection.json')
    args = parser.parse_args()

    try:
        if args.report:
            run_report_only()
        elif args.context:
            run_context_only()
        else:
            run_full()
    except Exception as e:
        print(f'\n[HIE] ERROR FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
