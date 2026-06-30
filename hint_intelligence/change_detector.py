"""
change_detector.py — Fase 2 del HIE.

Compara la KB actual contra la corrida anterior.
Si algo cambió más del umbral, genera una alerta.
Sin API. Todo comparación de JSON.
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


def run(patterns_new, patterns_old):
    """
    Compara patterns_new vs patterns_old.
    Devuelve lista de alertas. Lista vacía = sin cambios relevantes.
    """
    if not patterns_old:
        return []

    today = str(date.today())
    alerts = []

    # ── Cambio en dossier rate global ─────────────────────────────────────────
    new_g = patterns_new.get('global', {})
    old_g = patterns_old.get('global', {})
    if new_g and old_g:
        delta = new_g.get('dossier_pct', 0) - old_g.get('dossier_pct', 0)
        if abs(delta) >= config.CHANGE_ALERT_THRESHOLD_PCT and new_g.get('n', 0) >= config.MIN_N_FOR_CHANGE_ALERT:
            alerts.append({
                'id': 'CHG_GLOBAL_DOSSIER',
                'tipo': 'GLOBAL_CHANGE',
                'severidad': 'ALTA' if abs(delta) >= 15 else 'MEDIA',
                'titulo': f"Tasa de dossier global cambió {delta:+.1f}pp ({old_g['dossier_pct']}% → {new_g['dossier_pct']}%)",
                'anterior': old_g.get('dossier_pct'),
                'actual': new_g.get('dossier_pct'),
                'delta_pp': round(delta, 1),
                'n_anterior': old_g.get('n', 0),
                'n_actual': new_g.get('n', 0),
                'fecha': today,
            })

    # ── Cambios por sector ────────────────────────────────────────────────────
    new_sectors = patterns_new.get('por_sector', {})
    old_sectors = patterns_old.get('por_sector', {})

    for sector in new_sectors:
        ns = new_sectors[sector]
        os_ = old_sectors.get(sector, {})
        if not os_:
            # Sector nuevo que apareció
            if ns['n'] >= config.MIN_N_FOR_CHANGE_ALERT:
                alerts.append({
                    'id': f'CHG_NEW_SECTOR_{sector[:20]}',
                    'tipo': 'NEW_SECTOR',
                    'severidad': 'INFO',
                    'titulo': f"Sector nuevo detectado: {sector} (n={ns['n']}, {ns['dossier_pct']}% dossier)",
                    'sector': sector,
                    'n_actual': ns['n'],
                    'dossier_pct_actual': ns['dossier_pct'],
                    'fecha': today,
                })
            continue

        delta = ns['dossier_pct'] - os_.get('dossier_pct', 0)
        n_min = min(ns['n'], os_.get('n', 0))
        if abs(delta) >= config.CHANGE_ALERT_THRESHOLD_PCT and n_min >= config.MIN_N_FOR_CHANGE_ALERT:
            direccion = 'subió' if delta > 0 else 'bajó'
            sev = 'ALTA' if abs(delta) >= 15 else 'MEDIA'
            alerts.append({
                'id': f'CHG_SECTOR_{sector[:20]}',
                'tipo': 'SECTOR_CHANGE',
                'severidad': sev,
                'titulo': f"{sector} {direccion} {abs(delta):.1f}pp ({os_['dossier_pct']}% → {ns['dossier_pct']}%)",
                'sector': sector,
                'anterior': os_.get('dossier_pct'),
                'actual': ns['dossier_pct'],
                'delta_pp': round(delta, 1),
                'n_anterior': os_.get('n', 0),
                'n_actual': ns['n'],
                'fecha': today,
            })

    # ── Cambios en rendimiento de variantes ───────────────────────────────────
    new_var = patterns_new.get('por_variante', {})
    old_var = patterns_old.get('por_variante', {})

    for variante in new_var:
        nv = new_var[variante]
        ov = old_var.get(variante, {})
        if not ov:
            continue
        delta = nv['dossier_pct'] - ov.get('dossier_pct', 0)
        n_min = min(nv['n'], ov.get('n', 0))
        if abs(delta) >= config.CHANGE_ALERT_THRESHOLD_PCT and n_min >= 20:
            direccion = 'mejoró' if delta > 0 else 'empeoró'
            alerts.append({
                'id': f'CHG_VARIANTE_{variante}',
                'tipo': 'VARIANTE_CHANGE',
                'severidad': 'MEDIA',
                'titulo': f"Variante {variante} {direccion} {abs(delta):.1f}pp ({ov['dossier_pct']}% → {nv['dossier_pct']}%)",
                'variante': variante,
                'anterior': ov.get('dossier_pct'),
                'actual': nv['dossier_pct'],
                'delta_pp': round(delta, 1),
                'fecha': today,
            })

    # ── Cambios en objeciones ─────────────────────────────────────────────────
    new_obj = patterns_new.get('por_objecion', {})
    old_obj = patterns_old.get('por_objecion', {})

    # Objeción que creció significativamente
    for obj in new_obj:
        n_new = new_obj[obj]['n']
        n_old = old_obj.get(obj, {}).get('n', 0)
        if n_new >= 5 and n_old > 0:
            growth = ((n_new - n_old) / n_old) * 100
            if growth >= 50:
                alerts.append({
                    'id': f'CHG_OBJECION_{obj[:20]}',
                    'tipo': 'OBJECTION_GROWTH',
                    'severidad': 'MEDIA',
                    'titulo': f"Objecion '{obj}' creció {growth:.0f}% (n: {n_old} → {n_new})",
                    'objecion': obj,
                    'n_anterior': n_old,
                    'n_actual': n_new,
                    'crecimiento_pct': round(growth, 1),
                    'fecha': today,
                })

    # Ordenar por severidad
    sev_order = {'ALTA': 0, 'MEDIA': 1, 'INFO': 2}
    alerts.sort(key=lambda a: sev_order.get(a.get('severidad', 'INFO'), 9))

    return alerts


def save_alerts(alerts):
    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    _save_json(config.OUT_ALERTS, {
        'generado': str(date.today()),
        'n_alertas': len(alerts),
        'alertas': alerts,
    })
    return alerts
