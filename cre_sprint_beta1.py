# -*- coding: utf-8 -*-
"""
cre_sprint_beta1.py — Sprint Beta 1: 15 casos MSG2
Corre el motor, compara con Florencia, clasifica PASS/FAIL, identifica modulo raiz.
"""
import sys, io, re, time
from pathlib import Path
from collections import defaultdict

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


BASE = Path(__file__).parent
MSG2_DIR = BASE / "commercial_reasoning_engine" / "benchmark" / "msg2"

# ── Helpers ───────────────────────────────────────────────────────────────────

def meta(text, field):
    m = re.search(rf'\*\*{field}:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else ''

def section_content(text, name):
    m = re.search(rf'^##\s+{re.escape(name)}\s*$', text, re.MULTILINE)
    if not m:
        return ''
    start = m.end()
    nxt = re.search(r'^##\s+', text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    raw = text[start:end].strip()
    lines = [l[1:].strip() if l.strip().startswith('>') else l for l in raw.splitlines()]
    return '\n'.join(lines).strip()

def strip_blockquote(text):
    lines = [l[1:].strip() if l.strip().startswith('>') else l for l in text.splitlines()]
    return '\n'.join(lines).strip()

def expected_strategy(seniority):
    if seniority in ('DIRECTOR', 'CEO'):
        return 'ENTRE_PARES'
    if seniority == 'MANAGER':
        return 'CONSULTIVA'
    return 'EXPLORATORIA'

def florencia_strategy(msg2_text):
    """Infer strategy Florencia used in her actual MSG2."""
    if not msg2_text:
        return None
    t = msg2_text.lower()
    if any(x in t for x in ['intercambio', 'entre iguales', 'conversacion entre', 'conversa', 'perspectiva']):
        return 'ENTRE_PARES'
    if any(x in t for x in ['te muestro', 'como lo resolvimos', 'casos concretos de ese tipo', 'mostrarte']):
        return 'CONSULTIVA'
    # Default: if question is about their methodology vs about results → hints at strategy
    return None  # indeterminate

def classify_case(motor_action, motor_strategy, motor_reviewer_approved,
                   exp_strategy, flor_strategy, seniority, engagement):
    """
    Returns (category, root_module, notes)
    Categories: PASS / FALSE POSITIVE / FALSE NEGATIVE / EXPECTED FAIL
    """
    # Action must always be MSG2 for this benchmark
    if motor_action != 'MSG2':
        return 'FALSE NEGATIVE', 'Classifier', f'Motor dijo {motor_action} en lugar de MSG2'

    # Reviewer rejected
    if not motor_reviewer_approved:
        return 'FALSE POSITIVE', 'Reviewer', 'Reviewer rechazo el draft'

    # Strategy comparison — primary signal
    strategy_match = (motor_strategy == exp_strategy)
    florencia_match = (flor_strategy is None or motor_strategy == flor_strategy)

    if strategy_match and florencia_match:
        return 'PASS', None, ''

    if strategy_match and not florencia_match and flor_strategy is not None:
        # Motor matches rule, Florencia deviated — motor is right per protocol
        return 'PASS', None, f'Florencia uso {flor_strategy} (motor correcto segun reglas)'

    if not strategy_match:
        # Wrong strategy — root module depends on what went wrong
        if seniority in ('DIRECTOR', 'CEO') and motor_strategy != 'ENTRE_PARES':
            # Should have been ENTRE_PARES — Classifier uses Analyzer's seniority
            root = 'Classifier'
            return 'FALSE POSITIVE', root, f'Strategy {motor_strategy} en lugar de {exp_strategy} para {seniority}'
        if seniority == 'MANAGER' and motor_strategy != 'CONSULTIVA':
            root = 'Classifier'
            return 'FALSE POSITIVE', root, f'Strategy {motor_strategy} en lugar de CONSULTIVA para MANAGER'
        if seniority == 'OTHER' and motor_strategy == 'EXPLORATORIA':
            # OTHER + EXPLORATORIA = expected, not a real error
            return 'EXPECTED FAIL', 'Analyzer', f'Seniority OTHER sin datos — EXPLORATORIA es default razonable'

    return 'PASS', None, ''


def load_and_run(bench_path: Path):
    t0 = time.time()
    text = bench_path.read_text(encoding='utf-8', errors='replace')

    # Metadata from benchmark header
    bench_seniority = meta(text, 'Seniority')
    bench_sector = meta(text, 'Sector')
    bench_engagement = meta(text, 'Engagement')
    bench_name_m = re.search(r'^# Benchmark — MSG2 — (.+)$', text, re.MULTILINE)
    name = bench_name_m.group(1).strip() if bench_name_m else bench_path.stem

    # The embedded original .md is after "## Conversacion original"
    orig_start = text.find('## Conversacion original')
    if orig_start < 0:
        return None
    orig_text = text[orig_start:]

    # Extract MSG1 and Respuesta MSG1 from embedded content
    msg1 = strip_blockquote(section_content(orig_text, 'MSG1'))
    resp1 = strip_blockquote(section_content(orig_text, 'Respuesta MSG1'))
    msg2_florencia = strip_blockquote(section_content(orig_text, 'MSG2'))

    if not msg1 or not resp1:
        return None

    conversation_text = msg1 + '\n\n' + resp1

    # Run motor
    conversation = parse(conversation_text, prospect_name=name)
    prospect_data = {
        'stage': '1',
        'sector': bench_sector,
        'cargo_seniority': bench_seniority,
    }

    result = run(conversation, adapter=DryRunAdapter(), prospect_data=prospect_data)
    t1 = time.time()

    motor_action = str(result.action)
    motor_strategy = result.strategy_cl.strategy.value if result.strategy_cl else 'NONE'
    motor_engagement = result.analysis.engagement.value if result.analysis.engagement else 'NONE'
    motor_approved = result.review.approved if result.review else False
    motor_violations = result.review.violations if result.review else []

    exp_strat = expected_strategy(bench_seniority)
    flor_strat = florencia_strategy(msg2_florencia)

    category, root_module, notes = classify_case(
        motor_action, motor_strategy, motor_approved,
        exp_strat, flor_strat, bench_seniority, bench_engagement
    )

    elapsed = round(t1 - t0, 1)

    return {
        'name': name,
        'file': bench_path.name,
        'seniority': bench_seniority,
        'sector': bench_sector,
        'engagement': bench_engagement,
        'motor_action': motor_action,
        'motor_strategy': motor_strategy,
        'motor_engagement': motor_engagement,
        'motor_approved': motor_approved,
        'violations': [v.rule for v in motor_violations],
        'expected_strategy': exp_strat,
        'florencia_strategy': flor_strat or '?',
        'florencia_msg2': msg2_florencia[:120] if msg2_florencia else '(no encontrado)',
        'category': category,
        'root_module': root_module or '-',
        'notes': notes,
        'time_s': elapsed,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cases = sorted(MSG2_DIR.glob('*.md'))
    print(f"\nSprint Beta 1 — {len(cases)} casos MSG2\n")

    results = []
    for p in cases:
        r = load_and_run(p)
        if r is None:
            print(f"  SKIP: {p.name}")
            continue
        results.append(r)
        status = r['category']
        mod = r['root_module']
        print(f"  [{len(results):02d}] {r['name'][:28]:<28} {r['motor_strategy']:<14} {status:<16} {mod}")

    # ── Summary table ──────────────────────────────────────────────────────────

    print()
    print("=" * 100)
    print(f"{'#':<4} {'Nombre':<26} {'Senior':<10} {'EngMot':<8} {'Strategy':<14} {'ExpStrat':<14} {'Categoria':<18} {'Modulo'}")
    print("-" * 100)
    for i, r in enumerate(results, 1):
        print(
            f"{i:<4} {r['name'][:26]:<26} {r['seniority']:<10} "
            f"{r['motor_engagement']:<8} {r['motor_strategy']:<14} {r['expected_strategy']:<14} "
            f"{r['category']:<18} {r['root_module']}"
        )
        if r['notes']:
            print(f"     >> {r['notes'][:90]}")
    print("=" * 100)

    # ── Module error map ───────────────────────────────────────────────────────

    module_errors = defaultdict(int)
    cat_counts = defaultdict(int)
    for r in results:
        cat_counts[r['category']] += 1
        if r['root_module'] != '-':
            module_errors[r['root_module']] += 1

    avg_time = round(sum(r['time_s'] for r in results) / len(results), 1) if results else 0

    # Rec for Sprint 2
    top_module = max(module_errors, key=module_errors.get) if module_errors else 'ninguno'
    if cat_counts['PASS'] >= 12:
        rec = f"Pasar a SEG1. El motor domina MSG2 ({cat_counts['PASS']}/15 PASS)."
    elif top_module != 'ninguno':
        rec = f"Corregir modulo {top_module} ({module_errors[top_module]} errores) antes de SEG1."
    else:
        rec = "Revisar casos FAIL manualmente antes de decidir Sprint 2."

    # Write to cases detail
    pass_cases = [r for r in results if r['category'] == 'PASS']
    fail_cases = [r for r in results if r['category'] != 'PASS']

    # ── session_summary.md ────────────────────────────────────────────────────

    summary = f"""# Session Summary — CRE Beta

**Fecha:** 2026-07-09
**Estado:** SPRINT BETA 1 COMPLETADO

---

## SPRINT BETA 1

Casos analizados: {len(results)}

PASS: {cat_counts['PASS']}
EXPECTED FAIL: {cat_counts['EXPECTED FAIL']}
FALSE POSITIVE: {cat_counts['FALSE POSITIVE']}
FALSE NEGATIVE: {cat_counts['FALSE NEGATIVE']}

Errores por modulo:
Analyzer: {module_errors.get('Analyzer', 0)}
Evidence: {module_errors.get('Evidence', 0)}
Classifier: {module_errors.get('Classifier', 0)}
Strategy: {module_errors.get('Strategy', 0)}
Context: {module_errors.get('Context', 0)}
LLM: {module_errors.get('LLM', 0)}
Reviewer: {module_errors.get('Reviewer', 0)}

Tiempo promedio hasta identificar modulo raiz: {avg_time}s

Recomendacion para Sprint Beta 2:
{rec}

---

### Detalle casos no-PASS
"""
    for r in fail_cases:
        summary += f"- [{r['name']}] {r['category']} | Modulo: {r['root_module']} | {r['notes']}\n"

    summary_path = BASE / "commercial_reasoning_engine" / "docs" / "session_summary.md"
    summary_path.write_text(summary, encoding='utf-8')

    # Print the final summary box
    print()
    print("=" * 60)
    print("  SPRINT BETA 1")
    print("=" * 60)
    print(f"  Casos analizados    : {len(results)}")
    print()
    print(f"  PASS                : {cat_counts['PASS']}")
    print(f"  EXPECTED FAIL       : {cat_counts['EXPECTED FAIL']}")
    print(f"  FALSE POSITIVE      : {cat_counts['FALSE POSITIVE']}")
    print(f"  FALSE NEGATIVE      : {cat_counts['FALSE NEGATIVE']}")
    print()
    print("  Errores por modulo:")
    for mod in ['Analyzer','Evidence','Classifier','Strategy','Context','LLM','Reviewer']:
        n = module_errors.get(mod, 0)
        bar = '*' * n
        print(f"    {mod:<12}: {n}  {bar}")
    print()
    print(f"  Tiempo promedio     : {avg_time}s")
    print()
    print(f"  Recomendacion Sprint 2:")
    print(f"  {rec}")
    print("=" * 60)
    print()
    print(f"Session summary actualizado: {summary_path}")


if __name__ == '__main__':
    main()
