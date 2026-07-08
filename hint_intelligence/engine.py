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
import conversation_engine
import experiment_engine
import strategy_engine
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

    # ── 5b. Conversation engine ───────────────────────────────────────────────
    log('Ejecutando conversation_engine...')
    try:
        conv_result, conv_path = conversation_engine.run()
        cm = conv_result['metadata']
        log(f'  {cm["n_convertidos"]} convertidos vs {cm["n_no_convertidos"]} no convertidos analizados')
        spos = conv_result['señales_en_respuesta_prospecto']['signals_positive']
        sneg = conv_result['señales_en_respuesta_prospecto']['signals_negative']
        log(f'  Señales positivas: {len(spos)} | Señales negativas: {len(sneg)}')
    except Exception as e:
        log(f'  conversation_engine omitido: {e}')
        conv_result = None

    # ── 5c. Experiment engine ─────────────────────────────────────────────────
    log('Ejecutando experiment_engine...')
    exp_data, nuevos = experiment_engine.run(patterns)
    log(f'  {exp_data["metadata"]["n_pendientes"]} experimentos pendientes ({len(nuevos)} nuevos)')

    # ── 6. Context injection ──────────────────────────────────────────────────
    log('Generando context_injection.json...')
    knowledge_base.build_context_injection(sectors, patterns)

    # ── 7. Strategy brief ─────────────────────────────────────────────────────
    log('Generando strategy_brief.md...')
    conv_signals = {}
    if os.path.exists(config.KB_SIGNALS):
        with open(config.KB_SIGNALS, 'r', encoding='utf-8') as _f:
            conv_signals = json.load(_f)
    brief_path = strategy_engine.run(patterns, sectors, alerts, exp_data, conv_signals)
    log(f'  Brief: {brief_path}')

    # ── 8. Reporte ────────────────────────────────────────────────────────────
    log('Generando intelligence_report.md...')
    report_path = report_builder.build(patterns, sectors, objections, alerts, exp_data)
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

    # ── 9. Actualizar CLAUDE.md con inteligencia HIE ──────────────────────────
    update_claude_md_hie()

    return True


def update_claude_md_hie(context_path=None, claude_md_path=None):
    """Actualiza la sección INTELIGENCIA HIE en CLAUDE.md con datos frescos de context_injection.json."""
    if context_path is None:
        context_path = config.OUT_CONTEXT
    if claude_md_path is None:
        claude_md_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'CLAUDE.md')

    if not os.path.exists(context_path) or not os.path.exists(claude_md_path):
        log('update_claude_md_hie: archivo no encontrado, omitiendo')
        return

    with open(context_path, 'r', encoding='utf-8') as f:
        ctx = json.load(f)

    meta = ctx.get('metadata', {})
    fecha = meta.get('generado', 'desconocida')
    n_total = meta.get('n_total', 0)
    dr_global = meta.get('dossier_rate_global', 0)

    sectores = ctx.get('por_sector', {})
    variantes = ctx.get('variantes', {})
    seniorities = ctx.get('seniorities', {})

    # Construir filas de sectores con datos suficientes (n>=10)
    filas_sector = []
    for nombre, d in sorted(sectores.items(), key=lambda x: x[1].get('dossier_pct', 0), reverse=True):
        n = d.get('n', 0)
        if n < 10:
            continue
        pct = d.get('dossier_pct', 0)
        conf = d.get('confianza', '?')
        nota = ''
        if pct <= 15:
            nota = ' — bajo rendimiento'
        elif conf == 'MEDIUM' and pct >= 30:
            nota = ' — priorizar'
        filas_sector.append(f'| {nombre} | {pct}% | {n} | {conf}{nota} |')

    tabla_sector = '\n'.join(filas_sector) if filas_sector else '| (sin datos suficientes) | — | — | — |'

    # Seniorities
    filas_sen = []
    for nombre, d in sorted(seniorities.items(), key=lambda x: x[1].get('dossier_pct', 0), reverse=True):
        n = d.get('n', 0)
        pct = d.get('dossier_pct', 0)
        filas_sen.append(f'| {nombre} | {pct}% | {n} |')
    tabla_sen = '\n'.join(filas_sen)

    # Variantes
    filas_var = []
    for nombre, d in sorted(variantes.items(), key=lambda x: x[1].get('dossier_pct', 0), reverse=True):
        n = d.get('n', 0)
        pct = d.get('dossier_pct', 0)
        filas_var.append(f'| {nombre} | {pct}% | {n} |')
    tabla_var = '\n'.join(filas_var)

    # CEO vs Director para insight
    ceo_pct = seniorities.get('CEO', {}).get('dossier_pct', '?')
    dir_pct = seniorities.get('DIRECTOR', {}).get('dossier_pct', '?')
    var_a = variantes.get('A', {}).get('dossier_pct', '?')
    var_c = variantes.get('C', {}).get('dossier_pct', '?')

    nueva_seccion = f"""---

# INTELIGENCIA HIE (actualizado {fecha}, n={n_total})

Datos reales de conversiones. Usar para priorizar sectores, seniority y variante.

**Tasa global de dossier: {dr_global}%**

## Por sector (solo sectores con n>=10)

| Sector | Dossier % | n | Confianza |
|--------|-----------|---|-----------|
{tabla_sector}

Sectores con n<10: datos insuficientes, no tomar como referencia.

## Por seniority

| Seniority | Dossier % | n |
|-----------|-----------|---|
{tabla_sen}

**Regla derivada:** Preferir Director o Manager como primer contacto. CEO en frío convierte a {ceo_pct}% vs Director {dir_pct}%. Solo escalar a CEO si el Director lo sugiere.

## Por variante de MSG1

| Variante | Dossier % | n |
|----------|-----------|---|
{tabla_var}

**Regla derivada:** Siempre Variante A por defecto. Variante A tiene {var_a}% vs C {var_c}%.

## Insights críticos

1. **CEO en frio rinde mal ({ceo_pct}%)** — primer contacto en empresa nueva: preferir Director/Manager.
2. **Variante A gana claramente** — ya es default, mantener.
3. **Sectores con dossier_pct bajo 15% no son prioridad de outreach nuevo.**

---

*Esta seccion se actualiza automaticamente al correr `python hint_intelligence/engine.py`*"""

    with open(claude_md_path, 'r', encoding='utf-8') as f:
        contenido = f.read()

    MARCA_INICIO = '# INTELIGENCIA HIE'
    MARCA_SEPARADOR = '\n---\n\n# INTELIGENCIA HIE'

    if MARCA_INICIO in contenido:
        # Reemplazar desde el separador previo hasta el final
        idx = contenido.find(MARCA_SEPARADOR)
        if idx == -1:
            idx = contenido.find('\n# INTELIGENCIA HIE')
        if idx != -1:
            contenido = contenido[:idx] + '\n' + nueva_seccion
        else:
            # fallback: desde el encabezado
            idx = contenido.find('# INTELIGENCIA HIE')
            contenido = contenido[:idx] + nueva_seccion[4:]  # skip leading ---\n
    else:
        contenido = contenido.rstrip() + '\n\n' + nueva_seccion

    with open(claude_md_path, 'w', encoding='utf-8') as f:
        f.write(contenido)

    log(f'CLAUDE.md actualizado con inteligencia HIE (n={n_total}, {fecha})')


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
    update_claude_md_hie()
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
