"""
pattern_engine.py — Fase 1 del HIE.

Lee historial_dataset.json (fuente primaria, 427 contactos) y dataset.json
(fuente secundaria, conversaciones/*.md con ENGAGEMENT y OBJECION) y calcula
patrones de conversión con n_casos y nivel de confianza.

Nunca inventa. Si n < MIN_N_FOR_REPORT, el patrón no se incluye.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


# ── Helpers ───────────────────────────────────────────────────────────────────

def pct(n, total):
    return round(100 * n / total, 1) if total else 0.0


def confidence_label(n):
    for label, (lo, hi) in config.CONFIDENCE_THRESHOLDS.items():
        if lo <= n <= hi:
            return label
    return 'INSUFFICIENT'


def group_by(records, field):
    groups = defaultdict(list)
    for r in records:
        key = (r.get(field) or '').strip() or '(sin dato)'
        groups[key].append(r)
    return dict(groups)


def conversion_stats(records):
    """Calcula tasas de conversión a cada etapa para una lista de registros."""
    n = len(records)
    if n == 0:
        return {}
    respondio   = sum(1 for r in records if r.get('RESPONDIO') == 'SI')
    dossier     = sum(1 for r in records if r.get('DOSSIER_ENVIADO') == 'SI')
    seg         = sum(1 for r in records if r.get('SEG_ENVIADO') == 'SI')
    avanzado    = sum(1 for r in records if r.get('RESULTADO') == 'REUNION/AVANZADO')
    return {
        'n': n,
        'respondio_n': respondio,
        'respondio_pct': pct(respondio, n),
        'dossier_n': dossier,
        'dossier_pct': pct(dossier, n),
        'seg_n': seg,
        'seg_pct': pct(seg, n),
        'avanzado_n': avanzado,
        'avanzado_pct': pct(avanzado, n),
        'confianza': confidence_label(n),
    }


def build_pattern(dimension, value, stats, extra=None):
    """Construye un dict de insight estandarizado."""
    p = {
        'dimension': dimension,
        'valor': value,
        'n': stats['n'],
        'confianza': stats['confianza'],
        'respondio_pct': stats['respondio_pct'],
        'dossier_pct': stats['dossier_pct'],
        'seg_pct': stats['seg_pct'],
        'avanzado_pct': stats['avanzado_pct'],
        'fecha': str(date.today()),
        'version': 1,
    }
    if extra:
        p.update(extra)
    return p


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_historial_dataset():
    with open(config.HISTORIAL_DATASET, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_dataset_json():
    """Dataset de conversaciones/.md — tiene ENGAGEMENT_LEVEL y OBJECION_PRINCIPAL."""
    if not os.path.exists(config.DATASET_JSON):
        return []
    with open(config.DATASET_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── Análisis principal ────────────────────────────────────────────────────────

def run(records_hist, records_ds):
    """
    records_hist: lista de dicts del historial_dataset.json (fuente primaria)
    records_ds:   lista de dicts del dataset.json (fuente secundaria)
    Devuelve dict con todas las categorías de patrones.
    """
    today = str(date.today())
    patterns = {
        'metadata': {
            'generado': today,
            'n_historial': len(records_hist),
            'n_dataset_md': len(records_ds),
            'version': 1,
        },
        'global': {},
        'por_sector': {},
        'por_seniority': {},
        'por_variante': {},
        'combos': {},
        'por_engagement': {},
        'por_objecion': {},
        'insights': [],
    }

    # ── Global ────────────────────────────────────────────────────────────────
    patterns['global'] = conversion_stats(records_hist)

    # ── Por sector ────────────────────────────────────────────────────────────
    for sector, recs in sorted(group_by(records_hist, 'SECTOR').items()):
        if len(recs) < config.MIN_N_FOR_REPORT:
            continue
        stats = conversion_stats(recs)
        patterns['por_sector'][sector] = build_pattern('SECTOR', sector, stats)

    # ── Por seniority ─────────────────────────────────────────────────────────
    for seniority, recs in sorted(group_by(records_hist, 'SENIORITY').items()):
        if len(recs) < config.MIN_N_FOR_REPORT:
            continue
        stats = conversion_stats(recs)
        patterns['por_seniority'][seniority] = build_pattern('SENIORITY', seniority, stats)

    # ── Por variante ──────────────────────────────────────────────────────────
    for variante, recs in sorted(group_by(records_hist, 'VARIANTE').items()):
        if not variante or variante == '(sin dato)':
            continue
        if len(recs) < config.MIN_N_FOR_REPORT:
            continue
        stats = conversion_stats(recs)
        patterns['por_variante'][variante] = build_pattern('VARIANTE', variante, stats)

    # ── Combos sector × seniority ─────────────────────────────────────────────
    combo_groups = defaultdict(list)
    for r in records_hist:
        sector   = (r.get('SECTOR') or '').strip()
        seniority = (r.get('SENIORITY') or '').strip()
        if sector and seniority and sector != '(sin dato)' and seniority != '(sin dato)':
            combo_groups[f'{sector} × {seniority}'].append(r)

    for combo, recs in sorted(combo_groups.items()):
        if len(recs) < 5:  # umbral más alto para combos
            continue
        stats = conversion_stats(recs)
        patterns['combos'][combo] = build_pattern('COMBO', combo, stats)

    # ── Por engagement (desde dataset.json/.md) ───────────────────────────────
    for eng, recs in sorted(group_by(records_ds, 'ENGAGEMENT_LEVEL').items()):
        if eng == '(sin dato)' or eng == 'N/A' or not eng:
            continue
        if len(recs) < config.MIN_N_FOR_REPORT:
            continue
        # dataset.json tiene RESULTADO_FINAL, no RESULTADO — adaptar
        n = len(recs)
        dossier  = sum(1 for r in recs if r.get('DOSSIER_ENVIADO') == 'SI')
        reunion  = sum(1 for r in recs if r.get('RESULTADO_FINAL') == 'REUNION')
        cliente  = sum(1 for r in recs if r.get('RESULTADO_FINAL') == 'CLIENTE')
        patterns['por_engagement'][eng] = {
            'dimension': 'ENGAGEMENT_LEVEL',
            'valor': eng,
            'n': n,
            'confianza': confidence_label(n),
            'dossier_pct': pct(dossier, n),
            'reunion_pct': pct(reunion, n),
            'cliente_pct': pct(cliente, n),
            'fecha': today,
            'version': 1,
        }

    # ── Por objeción principal ────────────────────────────────────────────────
    for obj, recs in sorted(group_by(records_ds, 'OBJECION_PRINCIPAL').items()):
        if obj in ('(sin dato)', '', 'NONE'):
            continue
        if len(recs) < config.MIN_N_FOR_REPORT:
            continue
        n = len(recs)
        patterns['por_objecion'][obj] = {
            'dimension': 'OBJECION_PRINCIPAL',
            'valor': obj,
            'n': n,
            'confianza': confidence_label(n),
            'fecha': today,
            'version': 1,
        }

    # ── Insights destacados ───────────────────────────────────────────────────
    patterns['insights'] = _build_insights(patterns)

    return patterns


def _build_insights(p):
    """Extrae insights accionables ordenados por impacto potencial."""
    insights = []
    today = str(date.today())

    # Mejor y peor sector (mín. 5 casos)
    sectores = {
        k: v for k, v in p['por_sector'].items()
        if v['n'] >= 5 and k != '(sin dato)'
    }
    if sectores:
        mejor = max(sectores.items(), key=lambda kv: kv[1]['dossier_pct'])
        peor  = min(sectores.items(), key=lambda kv: kv[1]['dossier_pct'])
        insights.append({
            'id': 'INS_BEST_SECTOR',
            'tipo': 'CONVERSION_PATTERN',
            'titulo': f"Mejor sector: {mejor[0]} ({mejor[1]['dossier_pct']}% dossier, n={mejor[1]['n']})",
            'confianza': mejor[1]['confianza'],
            'n': mejor[1]['n'],
            'accion': f"Priorizar contactos en {mejor[0]}",
            'fecha': today,
        })
        if peor[1]['dossier_pct'] == 0.0 and peor[1]['n'] >= 3:
            insights.append({
                'id': 'INS_ZERO_SECTOR',
                'tipo': 'WARNING',
                'titulo': f"Sector sin conversión: {peor[0]} (0% dossier, n={peor[1]['n']})",
                'confianza': peor[1]['confianza'],
                'n': peor[1]['n'],
                'accion': f"Revisar o pausar contactos en {peor[0]} hasta entender el patrón",
                'fecha': today,
            })

    # Variante A vs C
    var_a = p['por_variante'].get('A')
    var_c = p['por_variante'].get('C')
    if var_a and var_c:
        diff = var_a['dossier_pct'] - var_c['dossier_pct']
        if abs(diff) >= 5:
            ganador = 'A' if diff > 0 else 'C'
            perdedor = 'C' if diff > 0 else 'A'
            vg = p['por_variante'][ganador]
            vp = p['por_variante'][perdedor]
            insights.append({
                'id': 'INS_VARIANTE_WINNER',
                'tipo': 'CONVERSION_PATTERN',
                'titulo': f"Variante {ganador} supera a {perdedor}: {vg['dossier_pct']}% vs {vp['dossier_pct']}% dossier",
                'confianza': confidence_label(min(vg['n'], vp['n'])),
                'n_A': var_a['n'],
                'n_C': var_c['n'],
                'accion': f"Default Variante {ganador}. Aumentar casos de Variante {perdedor} para confirmar (n={vp['n']}, necesita ≥30 para confianza MEDIUM)",
                'fecha': today,
            })

    # CEO vs Director
    ceo  = p['por_seniority'].get('CEO')
    dire = p['por_seniority'].get('DIRECTOR')
    if ceo and dire and ceo['n'] >= 5 and dire['n'] >= 5:
        if dire['dossier_pct'] > ceo['dossier_pct'] + 5:
            insights.append({
                'id': 'INS_CEO_UNDERPERFORMS',
                'tipo': 'TARGETING_WARNING',
                'titulo': f"CEO convierte menos en frío: {ceo['dossier_pct']}% vs Director {dire['dossier_pct']}%",
                'confianza': confidence_label(min(ceo['n'], dire['n'])),
                'n_ceo': ceo['n'],
                'n_director': dire['n'],
                'accion': "Preferir Director/Manager como primer contacto. Escalar a CEO solo si el Director lo sugiere.",
                'fecha': today,
            })

    # Sectores con n insuficiente pero datos prometedores
    for sector, v in p['por_sector'].items():
        if 5 <= v['n'] < 15 and v['dossier_pct'] >= 30:
            insights.append({
                'id': f'INS_PROMISING_{sector.upper().replace("/","_")[:20]}',
                'tipo': 'EXPERIMENT_NEEDED',
                'titulo': f"{sector}: {v['dossier_pct']}% dossier pero n={v['n']} (insuficiente para confirmar)",
                'confianza': 'LOW',
                'n': v['n'],
                'accion': f"Aumentar volumen en {sector} para confirmar el patrón. Objetivo: n=30.",
                'fecha': today,
            })

    return insights
