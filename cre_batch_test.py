# -*- coding: utf-8 -*-
"""
cre_batch_test.py - Corre el motor CRE en batch sobre conversaciones/*.md

Uso:
    python cre_batch_test.py --n 13
    python cre_batch_test.py --n 13 --mes julio
    python cre_batch_test.py --file conversaciones/julio/silvia-rojas.md
"""
import sys
import io
import os
import re
import argparse
import random
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.llm.adapter import LLMAdapter
from commercial_reasoning_engine.run import run


class DryRunAdapter(LLMAdapter):
    def _call(self, prompt: str) -> str:
        return "[DRY RUN]"


# ── MD parser ─────────────────────────────────────────────────────────────────

_SECTION_RE = re.compile(r'^##\s+(.+)$', re.MULTILINE)

def _extract_sections(text: str) -> dict:
    """Split .md into sections by ## heading."""
    sections = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def _strip_blockquote(text: str) -> str:
    """Remove > prefix from blockquote lines."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('>'):
            line = line[1:].strip()
        lines.append(line)
    return '\n'.join(lines).strip()


def _meta(text: str, field: str) -> str:
    """Extract **Field:** value from header."""
    m = re.search(rf'\*\*{field}:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else ''


def _seniority_from_cargo(cargo: str) -> str:
    cargo_l = cargo.lower()
    if any(x in cargo_l for x in ['ceo', 'chief executive', 'presidente', 'fundador', 'founder']):
        return 'CEO'
    if any(x in cargo_l for x in ['director', 'vp ', 'vice president', 'vicepresidente']):
        return 'DIRECTOR'
    if any(x in cargo_l for x in ['manager', 'gerente', 'jefe', 'head of', 'lider']):
        return 'MANAGER'
    if any(x in cargo_l for x in ['specialist', 'especialista', 'analyst', 'analista', 'coordinator']):
        return 'SPECIALIST'
    return 'OTHER'


def _stage_from_estado(estado: str) -> str:
    e = estado.lower()
    if 'reunion' in e or 'reuni' in e or 'stage 6' in e:
        return '3'  # motor perspective: dossier was sent before reunion
    if 'seg1' in e or 'seguimiento 1' in e:
        return '4'
    if 'dossier' in e:
        return '3'
    if 'msg2' in e:
        return '2'
    if 'msg1' in e:
        return '1'
    return '1'


def load_conversation_md(path: Path) -> dict:
    """
    Returns dict with:
      name, cargo, sector, seniority, stage, estado,
      conversation_text (raw, ready for parser),
      has_response (bool), days_dossier (int or None)

    Stage logic:
    - Has Respuesta MSG1 but NO MSG2 sent yet -> stage=1 (motor writes MSG2)
    - Estado says 'MSG2 enviado' -> extract only MSG1+Respuesta, stage=1
    - Estado says 'dossier' -> full conv + stage=3 + days_dossier=5
    - Estado says 'SEG1' -> full conv + stage=4
    """
    text = path.read_text(encoding='utf-8', errors='replace')

    # Name from first # heading
    name_m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    name = name_m.group(1).strip() if name_m else path.stem

    cargo = _meta(text, 'Cargo')
    sector = _meta(text, 'Sector')
    estado = _meta(text, 'Estado')
    seniority = _seniority_from_cargo(cargo)
    estado_l = estado.lower()

    sections = _extract_sections(text)
    has_response = 'Respuesta MSG1' in sections

    days_dossier = None

    # Estado takes priority — determines the motor's current task
    if 'seg1' in estado_l or ('dossier' in estado_l and 'enviado' in estado_l):
        # Dossier was already sent — motor should generate SEG1
        block_order = ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']
        stage = '3'
        days_dossier = 5
    elif 'reunion' in estado_l or 'stage 6' in estado_l:
        # Meeting closed — motor should NOT be generating new messages
        block_order = ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']
        stage = '3'
        days_dossier = 5
    elif 'cerrada' in estado_l or 'descartad' in estado_l or 'no interesad' in estado_l:
        # Conversation closed — test motor behavior on closed conv
        block_order = ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']
        stage = '2'
    elif 'msg2' in estado_l and 'Respuesta MSG1' in sections:
        # MSG2 was sent based on MSG1 response — test motor decision from MSG1 response
        block_order = ['MSG1', 'Respuesta MSG1']
        stage = '1'
    elif 'Respuesta MSG2' in sections:
        # Prospect responded to MSG2 — motor decides follow-up
        block_order = ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']
        stage = '2'
    elif 'Respuesta MSG1' in sections:
        # Prospect responded to MSG1, we need to write MSG2
        block_order = ['MSG1', 'Respuesta MSG1']
        stage = '1'
    else:
        block_order = ['MSG1']
        stage = '0'

    conv_blocks = []
    for key in block_order:
        if key in sections:
            raw = _strip_blockquote(sections[key])
            if raw:
                conv_blocks.append(raw)

    conversation_text = '\n\n'.join(conv_blocks)

    return {
        'name': name,
        'cargo': cargo,
        'sector': sector,
        'seniority': seniority,
        'stage': stage,
        'estado': estado,
        'conversation_text': conversation_text,
        'has_response': has_response,
        'days_dossier': days_dossier,
        'path': path,
    }


# ── Motor runner ──────────────────────────────────────────────────────────────

def run_case(case: dict) -> dict:
    adapter = DryRunAdapter()
    conversation = parse(case['conversation_text'], prospect_name=case['name'])

    prospect_data = {
        'stage': case['stage'],
        'sector': case['sector'],
        'cargo_seniority': case['seniority'],
    }
    if case.get('days_dossier') is not None:
        prospect_data['days_since_dossier'] = case['days_dossier']

    try:
        result = run(conversation, adapter=adapter, prospect_data=prospect_data)
        return {
            'ok': True,
            'result': result,
            'error': None,
        }
    except Exception as e:
        return {
            'ok': False,
            'result': None,
            'error': str(e),
        }


# ── Output ────────────────────────────────────────────────────────────────────

def _fmt(val, width=14):
    s = str(val) if val else '(none)'
    return s[:width].ljust(width)


def print_table(rows: list) -> None:
    # Header
    print()
    print('=' * 110)
    header = (
        f"{'#':<3} "
        f"{'Nombre':<22} "
        f"{'Stage':<6} "
        f"{'Senior':<10} "
        f"{'Engagement':<11} "
        f"{'Accion':<8} "
        f"{'Estrategia':<14} "
        f"{'Reviewer':<10} "
        f"{'Error'}"
    )
    print(header)
    print('-' * 110)

    for i, row in enumerate(rows, 1):
        case = row['case']
        run_r = row['run']

        name = case['name'][:22]
        stage = case['stage']
        senior = case['seniority'][:10]

        if not run_r['ok']:
            print(f"{i:<3} {name:<22} {stage:<6} {senior:<10} ERROR: {run_r['error'][:60]}")
            continue

        result = run_r['result']
        a = result.analysis
        d = result.decision

        eng = a.engagement.value[:11] if a.engagement else '?'
        action = str(result.action)[:8]
        strategy = result.strategy_cl.strategy.value[:14] if result.strategy_cl else '?'
        reviewer = 'APROBADO' if (result.review and result.review.approved) else ('RECHAZADO' if result.review else '?')

        print(
            f"{i:<3} {name:<22} {stage:<6} {senior:<10} "
            f"{eng:<11} {action:<8} {strategy:<14} {reviewer:<10}"
        )

        # Violations
        if result.review and result.review.violations:
            for v in result.review.violations:
                print(f"    ! [{v.rule}] {v.description[:80]}")

    print('=' * 110)
    print()


def print_detail(i: int, case: dict, run_r: dict) -> None:
    print()
    print(f"  [{i}] {case['name']}")
    print(f"      Cargo  : {case['cargo'][:70]}")
    print(f"      Estado : {case['estado'][:70]}")
    print(f"      Stage  : {case['stage']}  Seniority: {case['seniority']}  Sector: {case['sector'][:30]}")

    if not run_r['ok']:
        print(f"      ERROR  : {run_r['error']}")
        return

    result = run_r['result']
    a = result.analysis
    d = result.decision

    print(f"      Engagement   : {a.engagement.value}")
    print(f"      Temperatura  : {a.temperature.value}")
    print(f"      Accion       : {result.action}")
    print(f"      Estrategia   : {result.strategy_cl.strategy.value if result.strategy_cl else '?'}")
    print(f"      Objetivo     : {d.unique_objective if d else '?'}")
    print(f"      Hint/Dossier : {d.mention_hint}/{d.mention_dossier if d else '?/?'}")
    print(f"      Reunion      : {d.propose_meeting if d else '?'}")
    if d and d.personal_win:
        print(f"      Win personal : {d.personal_win[:70]}")
    if d and d.new_angle:
        print(f"      Angulo       : {d.new_angle[:70]}")
    if d and d.reference_client:
        print(f"      Cliente ref  : {d.reference_client}")
    if result.review:
        rv = result.review
        estado_r = 'APROBADO' if rv.approved else 'RECHAZADO'
        print(f"      Reviewer     : {estado_r} (score {rv.score})")
        for v in rv.violations:
            print(f"        ! [{v.rule}] {v.description[:80]}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="CRE Batch Test")
    ap.add_argument('--n', type=int, default=10, help='Cuantos casos correr')
    ap.add_argument('--mes', default='julio', choices=['julio', 'junio', 'ambos'], help='Mes a usar')
    ap.add_argument('--file', default=None, help='Archivo .md especifico')
    ap.add_argument('--seed', type=int, default=42, help='Seed para reproducibilidad')
    ap.add_argument('--detail', action='store_true', help='Mostrar detalle por caso')
    ap.add_argument('--only-responses', action='store_true', default=True,
                    help='Solo casos con respuesta del prospecto (default: true)')
    args = ap.parse_args()

    base = Path(__file__).parent / 'conversaciones'

    if args.file:
        paths = [Path(args.file)]
    else:
        if args.mes == 'julio':
            paths = list((base / 'julio').glob('*.md'))
        elif args.mes == 'junio':
            paths = list((base / 'junio').glob('*.md'))
        else:
            paths = list((base / 'julio').glob('*.md')) + list((base / 'junio').glob('*.md'))

    # Load all
    cases = []
    for p in paths:
        try:
            c = load_conversation_md(p)
            if args.only_responses and not c['has_response']:
                continue
            cases.append(c)
        except Exception as e:
            pass

    # Sample
    random.seed(args.seed)
    if len(cases) > args.n:
        cases = random.sample(cases, args.n)

    print(f"\nCRE Batch Test — {len(cases)} casos — mes: {args.mes}")
    print(f"Seed: {args.seed} | Only-responses: {args.only_responses}")

    rows = []
    for i, case in enumerate(cases, 1):
        run_r = run_case(case)
        rows.append({'case': case, 'run': run_r})

        if args.detail:
            print_detail(i, case, run_r)

    print_table(rows)

    # Summary
    ok = sum(1 for r in rows if r['run']['ok'])
    errors = len(rows) - ok
    approved = sum(1 for r in rows if r['run']['ok'] and r['run']['result'].review and r['run']['result'].review.approved)
    rejected = sum(1 for r in rows if r['run']['ok'] and r['run']['result'].review and not r['run']['result'].review.approved)

    print(f"Resumen:")
    print(f"  Motor OK   : {ok}/{len(rows)}")
    print(f"  Errores    : {errors}")
    print(f"  Aprobados  : {approved}/{ok}")
    print(f"  Rechazados : {rejected}/{ok}")

    actions = {}
    strategies = {}
    engagements = {}
    for r in rows:
        if not r['run']['ok']:
            continue
        result = r['run']['result']
        a_key = str(result.action)
        actions[a_key] = actions.get(a_key, 0) + 1
        if result.strategy_cl:
            s_key = result.strategy_cl.strategy.value
            strategies[s_key] = strategies.get(s_key, 0) + 1
        if result.analysis.engagement:
            e_key = result.analysis.engagement.value
            engagements[e_key] = engagements.get(e_key, 0) + 1

    print(f"\n  Acciones   : {dict(sorted(actions.items()))}")
    print(f"  Estrategias: {dict(sorted(strategies.items()))}")
    print(f"  Engagements: {dict(sorted(engagements.items()))}")
    print()


if __name__ == '__main__':
    main()
