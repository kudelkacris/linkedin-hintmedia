"""
strategy_engine.py — HIE Fase 5 (parcial).

Genera un strategy_brief.md legible: qué sectores atacar esta semana,
qué evitar, experimentos activos, alertas. Sin API.
"""
import json
import os
from datetime import date

import config


def _load(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(patterns, sectors, alerts, exp_data, conv_signals):
    today = str(date.today())
    g = patterns.get('global', {})

    lines = [
        f'# HINT INTELLIGENCE — Strategy Brief',
        f'**{today}**  |  Base: {g.get("n",0)} contactos  |  Dossier global: {g.get("dossier_pct",0)}%',
        '',
    ]

    # ── ATACAR ESTA SEMANA ────────────────────────────────────────────────────
    lines += ['## ATACAR ESTA SEMANA', '']
    atacar = [
        (s, v) for s, v in patterns.get('por_sector', {}).items()
        if v.get('n', 0) >= 5 and v.get('dossier_pct', 0) >= 25 and s != '(sin dato)'
    ]
    atacar.sort(key=lambda x: -x[1]['dossier_pct'])

    if atacar:
        for s, v in atacar[:5]:
            conf = {'HIGH':'🟢','MEDIUM':'🟡','LOW':'🔴','INSUFFICIENT':'⚫'}.get(v['confianza'],'⚫')
            clientes = ', '.join(config.HINT_CLIENTS_BY_SECTOR.get(s, config.DEFAULT_CLIENTS))
            lines.append(f'- **{s}** {conf} — {v["dossier_pct"]}% dossier (n={v["n"]}) · Clientes: {clientes}')
    else:
        lines.append('- Sin sectores con confianza suficiente todavía.')
    lines.append('')

    # ── EVITAR / REVISAR ─────────────────────────────────────────────────────
    lines += ['## EVITAR O REVISAR', '']
    evitar = [
        (s, v) for s, v in patterns.get('por_sector', {}).items()
        if v.get('n', 0) >= 3 and v.get('dossier_pct', 0) < 15 and s != '(sin dato)'
    ]
    seniority = patterns.get('por_seniority', {})
    ceo = seniority.get('CEO', {})

    if evitar:
        for s, v in sorted(evitar, key=lambda x: x[1]['dossier_pct']):
            lines.append(f'- **{s}**: {v["dossier_pct"]}% dossier (n={v["n"]}) — bajo retorno')
    if ceo and ceo.get('n', 0) >= 5:
        lines.append(f'- **CEO en frío**: {ceo["dossier_pct"]}% — preferir Director/Manager como primer contacto')
    lines.append('')

    # ── VARIANTE RECOMENDADA ──────────────────────────────────────────────────
    var = patterns.get('por_variante', {})
    var_a = var.get('A', {})
    var_c = var.get('C', {})
    if var_a and var_c:
        ganador = 'A' if var_a.get('dossier_pct', 0) >= var_c.get('dossier_pct', 0) else 'C'
        lines += [
            '## VARIANTE RECOMENDADA', '',
            f'- Default: **Variante {ganador}** ({var_a.get("dossier_pct",0)}% vs C {var_c.get("dossier_pct",0)}%)',
            f'- Variante C: n={var_c.get("n",0)} — {"confianza suficiente" if var_c.get("n",0)>=30 else "muestra chica, seguir testeando"}',
            '',
        ]

    # ── SEÑALES QUE PREDICEN DOSSIER ─────────────────────────────────────────
    if conv_signals:
        lengths = conv_signals.get('longitud_como_predictor', {})
        eng = conv_signals.get('engagement_como_predictor', {})
        lines += ['## SEÑALES EN RESPUESTA DEL PROSPECTO', '']
        if lengths:
            lines.append(f'- Respuesta larga (>{lengths.get("conv_avg_chars",200)} chars): convierte más')
            lines.append(f'- Con pregunta: {lengths.get("conv_question_pct",0)}% conv vs {lengths.get("no_conv_question_pct",0)}% no conv')
        if eng:
            for nivel in ['HIGH', 'MEDIUM', 'LOW']:
                e = eng.get(nivel, {})
                if e:
                    lines.append(f'- Engagement {nivel}: {e.get("dossier_pct",0)}% dossier (n={e.get("n",0)})')
        lines.append('')

    # ── EXPERIMENTOS ACTIVOS ──────────────────────────────────────────────────
    pendientes = [e for e in exp_data.get('experimentos', []) if e['estado'] == 'PENDIENTE']
    if pendientes:
        lines += ['## EXPERIMENTOS EN CURSO', '']
        for e in sorted(pendientes, key=lambda x: {'ALTA':0,'MEDIA':1,'BAJA':2}.get(x.get('prioridad','BAJA'),9)):
            prio = {'ALTA':'[!]','MEDIA':'[~]','BAJA':'[·]'}.get(e.get('prioridad',''),'')
            lines.append(f'- {prio} **{e["id"]}**: {e["hipotesis"]}')
            lines.append(f'  Acción: {e["como_testear"]}')
            lines.append(f'  Progreso: {e.get("n_actual",0)}/{e.get("n_objetivo",0)} · Faltan {e.get("n_faltan",0)}')
        lines.append('')

    # ── ALERTAS ───────────────────────────────────────────────────────────────
    if alerts:
        lines += ['## ALERTAS ACTIVAS', '']
        for a in alerts:
            sev = {'ALTA':'[!]','MEDIA':'[~]','INFO':'[i]'}.get(a.get('severidad',''),'')
            lines.append(f'- {sev} {a["titulo"]}')
        lines.append('')

    # ── RESUMEN EJECUTIVO (1 párrafo) ─────────────────────────────────────────
    top_sector = atacar[0] if atacar else None
    worst_sector = evitar[0] if evitar else None
    n_exp = len(pendientes)

    lines += ['## RESUMEN EJECUTIVO', '']
    resumen = f'Esta semana el foco debe estar en '
    if top_sector:
        resumen += f'**{top_sector[0]}** ({top_sector[1]["dossier_pct"]}% dossier)'
    if worst_sector:
        resumen += f', evitando **{worst_sector[0]}** ({worst_sector[1]["dossier_pct"]}%). '
    resumen += f'Hay {n_exp} experimentos pendientes. '
    if var_a and var_c:
        resumen += f'Usar Variante A como default ({var_a.get("dossier_pct",0)}% vs C {var_c.get("dossier_pct",0)}%).'
    lines.append(resumen)
    lines.append('')
    lines.append('_Generado por Hint Intelligence Engine — Strategy Brief_')

    # Guardar
    brief_path = os.path.join(config.OUTPUTS_DIR, 'strategy_brief.md')
    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    with open(brief_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return brief_path
