"""
report_builder.py — Genera intelligence_report.md legible por humanos.
"""
from datetime import date
import os
import config


def pct_bar(pct, width=20):
    filled = int(round(pct / 100 * width))
    return '█' * filled + '░' * (width - filled)


def confidence_emoji(level):
    return {'HIGH': '🟢', 'MEDIUM': '🟡', 'LOW': '🔴', 'INSUFFICIENT': '⚫'}.get(level, '⚫')


def build(patterns, sectors, objections):
    today = str(date.today())
    g = patterns.get('global', {})
    lines = []

    lines += [
        f'# HINT INTELLIGENCE ENGINE — Reporte',
        f'**Generado:** {today}  |  **Total contactos:** {g.get("n", 0)}  |  **Versión KB:** {patterns.get("metadata", {}).get("version", 1)}',
        '',
        '---',
        '',
        '## EMBUDO GLOBAL',
        '',
        f'| Etapa | N | % |',
        f'|---|---|---|',
        f'| Respondió MSG1 | {g.get("respondio_n","?")} | {g.get("respondio_pct","?")}% |',
        f'| Dossier enviado | {g.get("dossier_n","?")} | {g.get("dossier_pct","?")}% |',
        f'| Seguimiento SEG | {g.get("seg_n","?")} | {g.get("seg_pct","?")}% |',
        f'| Avanzado/Reunión | {g.get("avanzado_n","?")} | {g.get("avanzado_pct","?")}% |',
        '',
        '---',
        '',
        '## SECTORES — Conversión a dossier',
        '',
        '| Sector | N | Resp% | Dossier% | Seg% | Confianza |',
        '|---|---|---|---|---|---|',
    ]

    sector_sorted = sorted(
        patterns.get('por_sector', {}).items(),
        key=lambda kv: kv[1]['dossier_pct'],
        reverse=True
    )
    for sector, p in sector_sorted:
        if sector == '(sin dato)':
            continue
        ci = confidence_emoji(p['confianza'])
        lines.append(
            f"| {sector} | {p['n']} | {p['respondio_pct']}% | "
            f"**{p['dossier_pct']}%** | {p['seg_pct']}% | {ci} {p['confianza']} |"
        )

    lines += [
        '',
        '---',
        '',
        '## VARIANTES MSG1',
        '',
        '| Variante | N | Resp% | Dossier% | Confianza |',
        '|---|---|---|---|---|',
    ]
    for var, p in sorted(patterns.get('por_variante', {}).items(),
                          key=lambda kv: kv[1]['dossier_pct'], reverse=True):
        ci = confidence_emoji(p['confianza'])
        lines.append(
            f"| Variante {var} | {p['n']} | {p['respondio_pct']}% | "
            f"**{p['dossier_pct']}%** | {ci} {p['confianza']} |"
        )

    lines += [
        '',
        '---',
        '',
        '## SENIORITY',
        '',
        '| Seniority | N | Resp% | Dossier% | Confianza |',
        '|---|---|---|---|---|',
    ]
    for sen, p in sorted(patterns.get('por_seniority', {}).items(),
                          key=lambda kv: kv[1]['dossier_pct'], reverse=True):
        if sen == '(sin dato)':
            continue
        ci = confidence_emoji(p['confianza'])
        lines.append(
            f"| {sen} | {p['n']} | {p['respondio_pct']}% | "
            f"**{p['dossier_pct']}%** | {ci} {p['confianza']} |"
        )

    lines += [
        '',
        '---',
        '',
        '## COMBOS (Sector × Seniority, mín. 5 casos)',
        '',
        '| Combo | N | Dossier% | Confianza |',
        '|---|---|---|---|',
    ]
    for combo, p in sorted(patterns.get('combos', {}).items(),
                             key=lambda kv: kv[1]['dossier_pct'], reverse=True):
        ci = confidence_emoji(p['confianza'])
        lines.append(f"| {combo} | {p['n']} | **{p['dossier_pct']}%** | {ci} {p['confianza']} |")

    # Engagement (desde dataset.json)
    if patterns.get('por_engagement'):
        lines += [
            '',
            '---',
            '',
            '## ENGAGEMENT LEVEL (desde conversaciones/.md)',
            '',
            '| Engagement | N | Dossier% | Reunión% | Confianza |',
            '|---|---|---|---|---|',
        ]
        for eng, p in sorted(patterns['por_engagement'].items(),
                               key=lambda kv: kv[1].get('dossier_pct', 0), reverse=True):
            ci = confidence_emoji(p['confianza'])
            lines.append(
                f"| {eng} | {p['n']} | **{p.get('dossier_pct', '?')}%** | "
                f"{p.get('reunion_pct', '?')}% | {ci} {p['confianza']} |"
            )

    # Objeciones
    if objections:
        lines += [
            '',
            '---',
            '',
            '## OBJECIONES MÁS FRECUENTES',
            '',
            '| Objeción | N | Confianza |',
            '|---|---|---|',
        ]
        for obj, p in sorted(objections.items(), key=lambda kv: kv[1]['n'], reverse=True):
            ci = confidence_emoji(p['confianza'])
            lines.append(f"| {obj} | {p['n']} | {ci} {p['confianza']} |")

    # Insights
    insights = patterns.get('insights', [])
    if insights:
        lines += [
            '',
            '---',
            '',
            '## INSIGHTS ACCIONABLES',
            '',
        ]
        for ins in insights:
            tipo_icon = {'CONVERSION_PATTERN': '📊', 'WARNING': '⚠️',
                          'TARGETING_WARNING': '🎯', 'EXPERIMENT_NEEDED': '🧪'}.get(ins['tipo'], '💡')
            lines += [
                f"### {tipo_icon} {ins['titulo']}",
                f"- **Confianza:** {confidence_emoji(ins['confianza'])} {ins['confianza']}",
                f"- **Acción:** {ins['accion']}",
                '',
            ]

    lines += [
        '---',
        '',
        '## LEYENDA DE CONFIANZA',
        '',
        '| Nivel | N casos | Significado |',
        '|---|---|---|',
        '| 🟢 HIGH | ≥ 100 | Regla establecida |',
        '| 🟡 MEDIUM | 30–99 | Patrón consistente |',
        '| 🔴 LOW | 10–29 | Hipótesis a confirmar |',
        '| ⚫ INSUFFICIENT | < 10 | Sin datos suficientes |',
        '',
        '_Generado por Hint Intelligence Engine — Fase 1: Observación_',
    ]

    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    report_path = config.OUT_REPORT
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return report_path
