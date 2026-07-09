# -*- coding: utf-8 -*-
"""cre_sprint_beta2.py — Sprint Beta 2: 8 casos SEG1"""
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
    def _call(self, prompt): return "[DRY RUN]"

BASE = Path(__file__).parent
SEG1_DIR = BASE / "commercial_reasoning_engine" / "benchmark" / "seg1"

def meta(text, field):
    m = re.search(rf'\*\*{field}:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else ''

def section(text, name):
    m = re.search(rf'^##\s+{re.escape(name)}\s*$', text, re.MULTILINE)
    if not m: return ''
    start = m.end()
    nxt = re.search(r'^##\s+', text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    raw = text[start:end].strip()
    return '\n'.join(l[1:].strip() if l.strip().startswith('>') else l for l in raw.splitlines()).strip()

def expected(seniority, engagement):
    """Expected (action, strategy, propose_meeting) for SEG1."""
    action = 'SEG1'
    if seniority in ('CEO', 'DIRECTOR'):
        strategy = 'ENTRE_PARES'
    elif seniority == 'MANAGER':
        strategy = 'CONSULTIVA'
    else:
        strategy = 'EXPLORATORIA'
    propose_meeting = engagement == 'HIGH'
    return action, strategy, propose_meeting

def classify(motor_action, motor_strategy, motor_meeting, motor_approved,
             exp_action, exp_strategy, exp_meeting, seniority, engagement):
    # Action wrong
    if motor_action != exp_action:
        return 'FALSE NEGATIVE', 'Classifier', f'Motor dijo {motor_action}, esperado {exp_action}'
    # Reviewer rejected
    if not motor_approved:
        return 'FALSE POSITIVE', 'Reviewer', 'Reviewer rechazo el draft'
    # Strategy wrong
    if motor_strategy != exp_strategy:
        if seniority in ('CEO', 'DIRECTOR') and motor_strategy != 'ENTRE_PARES':
            return 'FALSE POSITIVE', 'Classifier', f'Strategy {motor_strategy} para {seniority}, esperado ENTRE_PARES'
        if seniority == 'MANAGER' and motor_strategy != 'CONSULTIVA':
            return 'FALSE POSITIVE', 'Classifier', f'Strategy {motor_strategy} para MANAGER, esperado CONSULTIVA'
        if seniority == 'OTHER':
            return 'EXPECTED FAIL', 'Analyzer', f'OTHER seniority -> {motor_strategy} (EXPLORATORIA esperado, no critico)'
    # Meeting proposal wrong
    if exp_meeting and not motor_meeting:
        return 'FALSE POSITIVE', 'Strategy', f'Engagement HIGH pero motor no propone reunion'
    if not exp_meeting and motor_meeting:
        return 'FALSE POSITIVE', 'Strategy', f'Engagement {engagement} pero motor propone reunion innecesaria'
    return 'PASS', None, ''

def run_case(p):
    t0 = time.time()
    text = p.read_text(encoding='utf-8', errors='replace')
    orig = text[text.find('## Conversacion original'):]

    seniority = meta(text, 'Seniority')
    sector    = meta(text, 'Sector')
    engagement = meta(text, 'Engagement')
    name_m = re.search(r'—\s*([^—\n]+)\s*$', text, re.MULTILINE)
    name = name_m.group(1).strip() if name_m else p.stem

    # Build conversation: MSG1 + RespMSG1 + MSG2 (+ RespMSG2 if exists)
    blocks = []
    for s in ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']:
        c = section(orig, s)
        if c:
            blocks.append(c)
    if len(blocks) < 2:
        return None

    conv_text = '\n\n'.join(blocks)
    conversation = parse(conv_text, prospect_name=name)
    prospect_data = {
        'stage': '3',
        'sector': sector,
        'cargo_seniority': seniority,
        'days_since_dossier': 5,
    }

    result = run(conversation, adapter=DryRunAdapter(), prospect_data=prospect_data)
    elapsed = round(time.time() - t0, 1)

    motor_action   = str(result.action)
    motor_strategy = result.strategy_cl.strategy.value if result.strategy_cl else 'NONE'
    motor_eng      = result.analysis.engagement.value if result.analysis.engagement else 'NONE'
    motor_approved = result.review.approved if result.review else False
    motor_meeting  = result.decision.propose_meeting if result.decision else False
    motor_violations = [v.rule for v in result.review.violations] if result.review else []

    exp_action, exp_strategy, exp_meeting = expected(seniority, engagement)

    category, root_module, notes = classify(
        motor_action, motor_strategy, motor_meeting, motor_approved,
        exp_action, exp_strategy, exp_meeting, seniority, engagement
    )

    return {
        'name': name, 'seniority': seniority, 'sector': sector,
        'engagement': engagement,
        'motor_action': motor_action, 'motor_strategy': motor_strategy,
        'motor_eng': motor_eng, 'motor_meeting': motor_meeting,
        'motor_approved': motor_approved, 'violations': motor_violations,
        'exp_action': exp_action, 'exp_strategy': exp_strategy, 'exp_meeting': exp_meeting,
        'category': category, 'root_module': root_module or '-', 'notes': notes,
        'time_s': elapsed,
    }

def main():
    cases = sorted(SEG1_DIR.glob('*.md'))
    print(f"\nSprint Beta 2 — {len(cases)} casos SEG1\n")

    results = []
    for p in cases:
        r = run_case(p)
        if r is None:
            print(f"  SKIP: {p.name}")
            continue
        results.append(r)
        print(f"  [{len(results):02d}] {r['name'][:28]:<28} {r['motor_strategy']:<14} meeting={str(r['motor_meeting']):<6} {r['category']:<18} {r['root_module']}")

    print()
    print("=" * 108)
    print(f"{'#':<4}{'Nombre':<26}{'Senior':<10}{'Eng':<7}{'Strategy':<14}{'ExpStr':<14}{'Meet':<6}{'Categoria':<18}{'Modulo'}")
    print("-" * 108)
    for i, r in enumerate(results, 1):
        print(f"{i:<4}{r['name'][:26]:<26}{r['seniority']:<10}{r['engagement']:<7}"
              f"{r['motor_strategy']:<14}{r['exp_strategy']:<14}{str(r['motor_meeting']):<6}"
              f"{r['category']:<18}{r['root_module']}")
        if r['notes']:
            print(f"     >> {r['notes'][:90]}")
    print("=" * 108)

    cat_counts = defaultdict(int)
    module_errors = defaultdict(int)
    for r in results:
        cat_counts[r['category']] += 1
        if r['root_module'] != '-':
            module_errors[r['root_module']] += 1

    pass_n = cat_counts['PASS']
    fail_cases = [r for r in results if r['category'] != 'PASS']

    if pass_n == len(results):
        conclusion = "Cerebro comercial validado para SEG1. Pasar a evaluacion LLM."
    elif pass_n >= len(results) - 1:
        conclusion = f"1 fallo detectado ({fail_cases[0]['root_module']}). Validar antes de LLM."
    else:
        top = max(module_errors, key=module_errors.get)
        conclusion = f"{len(fail_cases)} fallos. Modulo raiz dominante: {top}. Corregir antes de LLM."

    # Update session_summary.md
    summary = f"""# Session Summary — CRE Beta

**Fecha:** 2026-07-09
**Estado:** SPRINT BETA 2 COMPLETADO

---

## SPRINT BETA 2

Casos analizados: {len(results)} (SEG1)

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

Conclusion: {conclusion}

---

### Detalle no-PASS
"""
    for r in fail_cases:
        summary += f"- [{r['name']}] {r['category']} | Modulo: {r['root_module']} | {r['notes']}\n"

    summary += """
---

Sprint Beta 1 (MSG2): 15/15 PASS
Sprint Beta 2 (SEG1): ver arriba

Proximos pasos:
- Si ambos limpios -> Sprint Beta 3 = evaluacion calidad LLM con --llm
- Comandos: python cre_sprint_beta1.py / cre_sprint_beta2.py / cre_batch_test.py
"""
    (BASE / "commercial_reasoning_engine" / "docs" / "session_summary.md").write_text(summary, encoding='utf-8')

    # Print final box
    print()
    print("=" * 55)
    print("  SPRINT BETA 2")
    print("=" * 55)
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
        print(f"    {mod:<12}: {n}  {'*' * n}")
    print()
    print(f"  Conclusion:")
    print(f"  {conclusion}")
    print("=" * 55)

if __name__ == '__main__':
    main()
