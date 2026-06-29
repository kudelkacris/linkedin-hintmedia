"""Cálculo de métricas y generación de stats.json + report.md a partir del dataset ya construido."""
import json
from collections import Counter


def pct(n, total):
    return round(100 * n / total, 1) if total else 0.0


def compute_stats(records):
    total = len(records)
    respondio_msg1 = sum(1 for r in records if r['RESPONDIO_MSG1'] == 'SI')
    dossier = sum(1 for r in records if r['DOSSIER_ENVIADO'] == 'SI')
    seguimiento = sum(1 for r in records if r['SEG1_ENVIADO'] == 'SI' or r['SEG2_ENVIADO'] == 'SI')
    reunion = sum(1 for r in records if r['RESULTADO_FINAL'] == 'REUNION')
    cliente = sum(1 for r in records if r['RESULTADO_FINAL'] == 'CLIENTE')

    def dist(field):
        c = Counter(r[field] for r in records if r[field])
        return dict(c.most_common())

    def conversion_by(field, target_results=('REUNION', 'CLIENTE')):
        """Tasa de conversión a reunión/cliente, agrupado por valor de field."""
        groups = {}
        for r in records:
            key = r[field] or '(sin dato)'
            groups.setdefault(key, {'total': 0, 'convertidos': 0})
            groups[key]['total'] += 1
            if r['RESULTADO_FINAL'] in target_results:
                groups[key]['convertidos'] += 1
        return {k: {'total': v['total'], 'convertidos': v['convertidos'], 'tasa_pct': pct(v['convertidos'], v['total'])}
                for k, v in groups.items()}

    stats = {
        'TOTAL_CONVERSACIONES': total,
        'RESPONSE_RATE_MSG1': pct(respondio_msg1, total),
        'DOSSIER_RATE': pct(dossier, total),
        'FOLLOWUP_RATE': pct(seguimiento, total),
        'MEETING_RATE': pct(reunion, total),
        'CLIENT_RATE': pct(cliente, total),
        'distribucion': {
            'SECTOR': dist('SECTOR'),
            'PAIS': dist('PAIS'),
            'CARGO': dist('CARGO'),
            'ENGAGEMENT_LEVEL': dist('ENGAGEMENT_LEVEL'),
            'OBJECION_PRINCIPAL': dist('OBJECION_PRINCIPAL'),
            'RESULTADO_FINAL': dist('RESULTADO_FINAL'),
            'VARIANTE_MSG1': dist('VARIANTE_MSG1'),
        },
        'conversion_por_sector': conversion_by('SECTOR'),
        'conversion_por_cargo': conversion_by('CARGO'),
        'conversion_por_engagement': conversion_by('ENGAGEMENT_LEVEL'),
        'conversion_por_variante': conversion_by('VARIANTE_MSG1'),
        'needs_ai_count': sum(1 for r in records if r.get('NEEDS_AI')),
    }
    return stats


def _top_table(dist, n=10):
    items = sorted(dist.items(), key=lambda kv: -kv[1])[:n]
    lines = ['| Valor | Cantidad |', '|---|---|']
    for k, v in items:
        lines.append(f'| {k} | {v} |')
    return '\n'.join(lines)


def _conv_table(conv, n=10):
    items = sorted(conv.items(), key=lambda kv: -kv[1]['total'])[:n]
    lines = ['| Valor | Total | Convertidos (reunión+cliente) | Tasa |', '|---|---|---|---|']
    for k, v in items:
        lines.append(f"| {k} | {v['total']} | {v['convertidos']} | {v['tasa_pct']}% |")
    return '\n'.join(lines)


def build_report_md(stats, records):
    sector_conv = stats['conversion_por_sector']
    cargo_conv = stats['conversion_por_cargo']
    ranked_sectors = {k: v for k, v in sector_conv.items() if k != '(sin dato)'}
    sorted_by_rate_desc = sorted(ranked_sectors.items(), key=lambda kv: -kv[1]['tasa_pct'] if kv[1]['total'] >= 3 else -999)
    sorted_by_rate_asc = sorted(ranked_sectors.items(), key=lambda kv: kv[1]['tasa_pct'] if kv[1]['total'] >= 3 else 999)

    lines = []
    lines.append('# Hint Intelligence Dataset — Reporte V1\n')
    lines.append(f"Total conversaciones procesadas: **{stats['TOTAL_CONVERSACIONES']}**")
    lines.append(f"Registros que necesitan revisión IA: **{stats['needs_ai_count']}**\n")

    lines.append('## Tasas globales\n')
    lines.append('| Métrica | Valor |')
    lines.append('|---|---|')
    lines.append(f"| Respuesta a MSG1 | {stats['RESPONSE_RATE_MSG1']}% |")
    lines.append(f"| Dossier enviado | {stats['DOSSIER_RATE']}% |")
    lines.append(f"| Seguimiento (SEG1/SEG2) | {stats['FOLLOWUP_RATE']}% |")
    lines.append(f"| Reunión agendada | {stats['MEETING_RATE']}% |")
    lines.append(f"| Cliente cerrado | {stats['CLIENT_RATE']}% |\n")

    lines.append('## Top sectores (por volumen)\n')
    lines.append(_top_table(stats['distribucion']['SECTOR']))
    lines.append('')

    lines.append('## Top cargos (por volumen)\n')
    lines.append(_top_table(stats['distribucion']['CARGO']))
    lines.append('')

    lines.append('## Objeciones más frecuentes\n')
    lines.append(_top_table(stats['distribucion']['OBJECION_PRINCIPAL']))
    lines.append('')

    lines.append('## Conversión por sector (mín. 3 casos para ranking)\n')
    lines.append(_conv_table(sector_conv))
    lines.append('')

    lines.append('## Conversión por cargo\n')
    lines.append(_conv_table(cargo_conv))
    lines.append('')

    lines.append('## Conversión por variante MSG1 (A vs C)\n')
    lines.append(_conv_table(stats['conversion_por_variante']))
    lines.append('')

    lines.append('## Conversión por nivel de engagement\n')
    lines.append(_conv_table(stats['conversion_por_engagement']))
    lines.append('')

    lines.append('## Perfiles con mayor conversión (sector, mín. 3 casos)\n')
    top_sectors = [kv for kv in sorted_by_rate_desc if kv[1]['total'] >= 3][:5]
    lines.append(_conv_table(dict(top_sectors), n=5))
    lines.append('')

    lines.append('## Perfiles con menor conversión (sector, mín. 3 casos)\n')
    bottom_sectors = [kv for kv in sorted_by_rate_asc if kv[1]['total'] >= 3][:5]
    lines.append(_conv_table(dict(bottom_sectors), n=5))
    lines.append('')

    lines.append('## Distribución por resultado final\n')
    lines.append(_top_table(stats['distribucion']['RESULTADO_FINAL']))
    lines.append('')

    return '\n'.join(lines)
