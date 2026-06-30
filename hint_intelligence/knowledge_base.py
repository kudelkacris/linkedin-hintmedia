"""
knowledge_base.py — Gestión de la KB del HIE.

Persiste los patrones detectados por el pattern_engine en archivos JSON
versionados. Si ya existe una versión anterior, la compara y detecta cambios.
"""
import json
import os
from datetime import date

import config


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _bump_version(new_data, old_data):
    """Si los datos cambiaron, incrementa la versión y registra el cambio."""
    old_n = old_data.get('metadata', {}).get('n_historial', 0)
    new_n = new_data.get('metadata', {}).get('n_historial', 0)
    old_ver = old_data.get('metadata', {}).get('version', 0)
    new_data['metadata']['version'] = old_ver + 1 if old_n != new_n else old_ver + 1
    new_data['metadata']['previous_n'] = old_n
    return new_data


def save_patterns(patterns):
    old = _load_json(config.KB_PATTERNS)
    if old:
        patterns = _bump_version(patterns, old)
    _save_json(config.KB_PATTERNS, patterns)


def build_sector_intelligence(patterns):
    """
    Construye sector_intelligence.json desde los patrones.
    Un objeto por sector con toda la info relevante para context_injection.
    """
    today = str(date.today())
    old = _load_json(config.KB_SECTORS)
    sectors = {}

    for sector, p in patterns.get('por_sector', {}).items():
        if sector == '(sin dato)':
            continue

        old_sector = old.get(sector, {})
        version = old_sector.get('version', 0) + 1

        # Mejor combo de seniority en este sector
        mejor_seniority = _best_seniority_for_sector(sector, patterns)
        mejor_variante  = _best_variante_for_sector(sector, patterns)

        sectors[sector] = {
            'sector': sector,
            'n_total': p['n'],
            'respondio_pct': p['respondio_pct'],
            'dossier_pct': p['dossier_pct'],
            'seg_pct': p['seg_pct'],
            'avanzado_pct': p['avanzado_pct'],
            'confianza': p['confianza'],
            'mejor_seniority': mejor_seniority,
            'mejor_variante': mejor_variante,
            'clientes_hint': config.HINT_CLIENTS_BY_SECTOR.get(sector, config.DEFAULT_CLIENTS),
            'ultima_actualizacion': today,
            'version': version,
        }

    _save_json(config.KB_SECTORS, sectors)
    return sectors


def _best_seniority_for_sector(sector, patterns):
    """Encuentra el seniority con mejor dossier_pct dentro de ese sector."""
    best = None
    best_pct = -1
    for combo, p in patterns.get('combos', {}).items():
        if combo.startswith(sector + ' × ') and p['n'] >= 5:
            if p['dossier_pct'] > best_pct:
                best_pct = p['dossier_pct']
                best = combo.split(' × ')[1]
    return best or 'INSUFFICIENT_DATA'


def _best_variante_for_sector(sector, patterns):
    """
    No tenemos variante por sector en el historial_dataset directamente.
    Por ahora retorna la variante global ganadora o INSUFFICIENT_DATA.
    """
    var = patterns.get('por_variante', {})
    if not var:
        return 'INSUFFICIENT_DATA'
    if len(var) < 2:
        k = list(var.keys())[0]
        return k if var[k]['n'] >= 10 else 'INSUFFICIENT_DATA'
    sorted_var = sorted(var.items(), key=lambda kv: kv[1]['dossier_pct'], reverse=True)
    winner = sorted_var[0]
    if winner[1]['n'] >= 10:
        return winner[0]
    return 'INSUFFICIENT_DATA'


def build_objection_playbook(patterns):
    """Persiste las objeciones detectadas con sus frecuencias."""
    today = str(date.today())
    old = _load_json(config.KB_OBJECTIONS)
    playbook = {}

    for obj, p in patterns.get('por_objecion', {}).items():
        old_entry = old.get(obj, {})
        playbook[obj] = {
            'objecion': obj,
            'n': p['n'],
            'confianza': p['confianza'],
            'respuesta_sugerida': old_entry.get('respuesta_sugerida', ''),
            'recuperable': old_entry.get('recuperable', None),
            'ultima_actualizacion': today,
            'version': old_entry.get('version', 0) + 1,
        }

    _save_json(config.KB_OBJECTIONS, playbook)
    return playbook


def build_context_injection(sectors, patterns):
    """
    Construye context_injection.json — el input que el servidor leerá
    para enriquecer el SYSTEM prompt en tiempo real.

    Formato pensado para ser consumido por generateOpeners() en index.html:
    dado sector + seniority, retorna lo que la IA necesita saber.
    """
    today = str(date.today())

    by_sector = {}
    for sector, s in sectors.items():
        by_sector[sector] = {
            'dossier_pct': s['dossier_pct'],
            'confianza': s['confianza'],
            'n': s['n_total'],
            'mejor_seniority': s['mejor_seniority'],
            'mejor_variante': s['mejor_variante'],
            'clientes_hint': s['clientes_hint'],
        }

    global_stats = patterns.get('global', {})
    variantes = {k: {'dossier_pct': v['dossier_pct'], 'n': v['n']}
                 for k, v in patterns.get('por_variante', {}).items()}
    seniorities = {k: {'dossier_pct': v['dossier_pct'], 'n': v['n']}
                   for k, v in patterns.get('por_seniority', {}).items()}

    context = {
        'metadata': {
            'generado': today,
            'n_total': global_stats.get('n', 0),
            'dossier_rate_global': global_stats.get('dossier_pct', 0),
        },
        'por_sector': by_sector,
        'variantes': variantes,
        'seniorities': seniorities,
        'insights_criticos': [
            i for i in patterns.get('insights', [])
            if i['tipo'] in ('TARGETING_WARNING', 'CONVERSION_PATTERN')
        ],
    }

    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    _save_json(config.OUT_CONTEXT, context)
    return context
