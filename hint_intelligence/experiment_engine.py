"""
experiment_engine.py — HIE Fase 4.

Detecta qué hipótesis no tienen evidencia suficiente y propone
experimentos concretos con n mínimo, cómo ejecutarlos y cómo
trackear el resultado. Sin API.
"""
import json
import os
from datetime import date

import config


MIN_N_TO_CONFIRM = 30   # n mínimo para considerar un patrón confirmado


def _load(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run(patterns):
    today = str(date.today())
    existing = _load(config.KB_EXPERIMENTS)
    existing_ids = {e['id'] for e in existing.get('experimentos', [])}
    nuevos = []

    # ── 1. Variante C — muestra insuficiente ──────────────────────────────────
    var = patterns.get('por_variante', {})
    var_c = var.get('C', {})
    var_a = var.get('A', {})
    if var_c and var_c.get('n', 0) < MIN_N_TO_CONFIRM:
        exp_id = 'EXP_VARIANTE_C'
        if exp_id not in existing_ids:
            nuevos.append({
                'id': exp_id,
                'estado': 'PENDIENTE',
                'prioridad': 'ALTA',
                'hipotesis': 'Variante C puede superar a Variante A en perfiles con señal de TRABAJO fuerte',
                'por_que': f'Variante C tiene solo {var_c["n"]} casos vs {var_a.get("n",0)} de A. '
                           f'La diferencia ({var_a.get("dossier_pct",0)}% vs {var_c.get("dossier_pct",0)}%) puede ser ruido estadístico.',
                'como_testear': f'Próximos {MIN_N_TO_CONFIRM - var_c["n"]} prospectos con señal clara de trabajo '
                                '(proyecto, expansión, operación) → usar Variante C exclusivamente.',
                'n_actual': var_c.get('n', 0),
                'n_objetivo': MIN_N_TO_CONFIRM,
                'n_faltan': max(0, MIN_N_TO_CONFIRM - var_c.get('n', 0)),
                'impacto_si_confirma': 'Si C iguala a A, duplicar su uso aumentaría diversificación sin perder conversión.',
                'riesgo': f'Sacrificamos conversión en {MIN_N_TO_CONFIRM - var_c["n"]} prospectos si la hipótesis es falsa.',
                'resultado': None,
                'fecha_creado': today,
                'fecha_resultado': None,
            })

    # ── 2. Sectores prometedores con n bajo ────────────────────────────────────
    for sector, p in patterns.get('por_sector', {}).items():
        if p.get('n', 0) < MIN_N_TO_CONFIRM and p.get('dossier_pct', 0) >= 30:
            exp_id = f'EXP_SECTOR_{sector[:15].upper().replace("/","_").replace(" ","_")}'
            if exp_id not in existing_ids:
                faltan = max(0, MIN_N_TO_CONFIRM - p['n'])
                nuevos.append({
                    'id': exp_id,
                    'estado': 'PENDIENTE',
                    'prioridad': 'MEDIA' if p['n'] >= 10 else 'BAJA',
                    'hipotesis': f'{sector} convierte al {p["dossier_pct"]}% — confirmar con más volumen',
                    'por_que': f'Solo {p["n"]} casos. Con n<{MIN_N_TO_CONFIRM} no es concluyente.',
                    'como_testear': f'Buscar y contactar {faltan} prospectos más en {sector}.',
                    'n_actual': p['n'],
                    'n_objetivo': MIN_N_TO_CONFIRM,
                    'n_faltan': faltan,
                    'impacto_si_confirma': f'Priorizar {sector} como sector de alto rendimiento.',
                    'riesgo': 'Bajo. Solo implica enfocar esfuerzo de búsqueda.',
                    'resultado': None,
                    'fecha_creado': today,
                    'fecha_resultado': None,
                })

    # ── 3. CEO en frío — ¿hay un approach que funcione? ──────────────────────
    ceo = patterns.get('por_seniority', {}).get('CEO', {})
    if ceo and ceo.get('n', 0) >= 5 and ceo.get('dossier_pct', 0) < 15:
        exp_id = 'EXP_CEO_APPROACH'
        if exp_id not in existing_ids:
            nuevos.append({
                'id': exp_id,
                'estado': 'PENDIENTE',
                'prioridad': 'MEDIA',
                'hipotesis': 'CEO convierte mejor si primero se conecta con alguien de su equipo (Director/Manager)',
                'por_que': f'CEO directo = {ceo["dossier_pct"]}% dossier (n={ceo["n"]}). '
                           'Posible que el approach indirecto sea más efectivo.',
                'como_testear': 'Próximos 10 CEOs: no contactar al CEO directamente. '
                                'Primero conectar con Director/Manager del área. '
                                'Trackear si la tasa de dossier sube.',
                'n_actual': 0,
                'n_objetivo': 10,
                'n_faltan': 10,
                'impacto_si_confirma': 'Cambiar la estrategia de targeting para empresas con CEO conocido.',
                'riesgo': 'Medio. Requiere más pasos en el proceso.',
                'resultado': None,
                'fecha_creado': today,
                'fecha_resultado': None,
            })

    # ── Combinar con existentes ────────────────────────────────────────────────
    todos = existing.get('experimentos', []) + nuevos
    kb_data = {
        'metadata': {
            'generado': today,
            'n_experimentos': len(todos),
            'n_pendientes': sum(1 for e in todos if e['estado'] == 'PENDIENTE'),
            'n_completados': sum(1 for e in todos if e['estado'] == 'COMPLETADO'),
        },
        'experimentos': todos,
    }
    _save(config.KB_EXPERIMENTS, kb_data)

    # Output legible
    output_path = config.OUT_EXPERIMENTS
    _save(output_path, kb_data)

    return kb_data, nuevos


def build_experiment_section(kb_data):
    """Genera sección markdown para el reporte del engine."""
    pendientes = [e for e in kb_data.get('experimentos', []) if e['estado'] == 'PENDIENTE']
    if not pendientes:
        return ''

    lines = ['', '---', '', '## EXPERIMENTOS PROPUESTOS', '']
    prio_order = {'ALTA': 0, 'MEDIA': 1, 'BAJA': 2}
    pendientes.sort(key=lambda e: prio_order.get(e.get('prioridad', 'BAJA'), 9))

    for e in pendientes:
        prio_icon = {'ALTA': '[!]', 'MEDIA': '[~]', 'BAJA': '[·]'}.get(e.get('prioridad'), '')
        progress = f"{e.get('n_actual',0)}/{e.get('n_objetivo',0)} casos"
        lines += [
            f"### {prio_icon} {e['id']}",
            f"**Hipótesis:** {e['hipotesis']}",
            f"**Por qué:** {e['por_que']}",
            f"**Cómo testear:** {e['como_testear']}",
            f"**Progreso:** {progress} · Faltan: {e.get('n_faltan',0)}",
            f"**Impacto si confirma:** {e['impacto_si_confirma']}",
            '',
        ]
    return '\n'.join(lines)
