# -*- coding: utf-8 -*-
"""
cre_sprint_beta3.py — Sprint Beta 3: LLM Quality
Corre el pipeline completo (CRE + Claude) sobre los 15 casos MSG2.
Compara mensajes generados vs mensajes reales de Florencia.
Clasifica: PASS / MINOR DIFFERENCE / FALSE POSITIVE / FALSE NEGATIVE

Requiere: ANTHROPIC_API_KEY en el entorno.
    Windows: $env:ANTHROPIC_API_KEY = "sk-ant-..."
    Linux:   export ANTHROPIC_API_KEY="sk-ant-..."
"""
import sys, io, os, re, time
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.run import run

BASE     = Path(__file__).parent
MSG2_DIR = BASE / "commercial_reasoning_engine" / "benchmark" / "msg2"

# ── Blocklist ─────────────────────────────────────────────────────────────────

BLOCKLIST = [
    "gracias por la apertura", "por la apertura", "con apertura",
    "por eso pensé en escribirte", "por eso te escribo", "te escribo porque",
    "es un desafío que vemos seguido",
    "justamente por eso", "exactamente donde trabajamos",
    "muchas empresas",
    "somos una agencia",
    "no sé si viste",
    "quedo atento", "quedo atenta",
    "cualquier duda",
    "más allá del dossier",
    "retomo", "vuelvo a escribirte",
    "no quería dejar de escribirte",
    "quería hacer seguimiento",
    "vi que sos", "veo que sos", "como responsable de", "como gerente de",
]

REQUIRED_ELEMENTS = [
    ("Buenas", "apertura con 'Buenas'"),
    ("Hint", "menciona Hint Media"),
    ("dossier", "menciona el dossier"),
    ("?", "incluye al menos una pregunta"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def meta(text, field):
    m = re.search(rf'\*\*{field}:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else ''

def sec(text, name):
    m = re.search(rf'^##\s+{re.escape(name)}\s*$', text, re.MULTILINE)
    if not m: return ''
    start = m.end()
    nxt = re.search(r'^##\s+', text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    raw = text[start:end].strip()
    return '\n'.join(l[1:].strip() if l.strip().startswith('>') else l for l in raw.splitlines()).strip()

def check_blocklist(msg):
    hits = [phrase for phrase in BLOCKLIST if phrase.lower() in msg.lower()]
    return hits

def check_required(msg):
    missing = [label for pattern, label in REQUIRED_ELEMENTS if pattern.lower() not in msg.lower()]
    return missing

def count_questions(msg):
    return msg.count('?')

def has_em_dash(msg):
    return '—' in msg or ' - ' in msg[:20]

def first_subject(msg):
    first_line = msg.split('\n')[0].strip()[:80]
    if any(x in first_line.lower() for x in ['trabajo en hint', 'en hint', 'somos', 'nosotros']):
        return 'HINT_FIRST'
    return 'OK'

def classify_quality(blocklist_hits, missing_required, q_count, em_dash, first_subj, reviewer_approved):
    issues = []

    if not reviewer_approved:
        return 'FALSE POSITIVE', ['Reviewer rechazo el mensaje']

    if blocklist_hits:
        return 'FALSE POSITIVE', [f'Blocklist: {", ".join(blocklist_hits[:2])}']

    if first_subj == 'HINT_FIRST':
        issues.append('Perspectiva: arranca desde Hint, no desde el prospecto')

    if missing_required:
        issues.append(f'Faltan: {", ".join(missing_required)}')

    if q_count == 0:
        issues.append('Sin pregunta final')
    elif q_count > 2:
        issues.append(f'Demasiadas preguntas ({q_count})')

    if em_dash:
        issues.append('Usa guion largo (—) — prohibido en formato')

    if issues:
        # Minor vs major
        if len(issues) <= 1 and not missing_required:
            return 'MINOR DIFFERENCE', issues
        return 'FALSE POSITIVE', issues

    return 'PASS', []

# ── LLM Runner ────────────────────────────────────────────────────────────────

def run_case(p, adapter):
    t0 = time.time()
    text = p.read_text(encoding='utf-8', errors='replace')
    orig = text[text.find('## Conversacion original'):]

    seniority = meta(text, 'Seniority')
    sector    = meta(text, 'Sector')
    name_m    = re.search(r'^# Benchmark.*?-- (.+)$', text, re.MULTILINE)
    name      = name_m.group(1).strip() if name_m else p.stem

    msg1  = sec(orig, 'MSG1')
    resp1 = sec(orig, 'Respuesta MSG1')
    florencia_msg2 = sec(orig, 'MSG2')

    if not msg1 or not resp1:
        return None

    conv = msg1 + '\n\n' + resp1
    conversation = parse(conv, prospect_name=name)
    prospect_data = {'stage': '1', 'sector': sector, 'cargo_seniority': seniority}

    result = run(conversation, adapter=adapter, prospect_data=prospect_data)
    elapsed = round(time.time() - t0, 1)

    generated = result.final_message or result.draft or ''
    reviewer_approved = result.review.approved if result.review else False
    reviewer_score    = result.review.score if result.review else 0
    violations = [v.rule for v in result.review.violations] if result.review else []

    blocklist_hits = check_blocklist(generated)
    missing        = check_required(generated)
    q_count        = count_questions(generated)
    em_dash        = has_em_dash(generated)
    first_subj     = first_subject(generated)

    category, issues = classify_quality(blocklist_hits, missing, q_count, em_dash, first_subj, reviewer_approved)

    return {
        'name': name,
        'seniority': seniority,
        'sector': sector,
        'motor_strategy': result.strategy_cl.strategy.value if result.strategy_cl else '?',
        'motor_engagement': result.analysis.engagement.value if result.analysis.engagement else '?',
        'reviewer_approved': reviewer_approved,
        'reviewer_score': reviewer_score,
        'violations': violations,
        'generated': generated,
        'florencia': florencia_msg2,
        'q_count': q_count,
        'blocklist_hits': blocklist_hits,
        'missing_required': missing,
        'issues': issues,
        'category': category,
        'time_s': elapsed,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print()
        print("ERROR: ANTHROPIC_API_KEY no encontrada.")
        print()
        print("Configurar antes de correr:")
        print('  Windows PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-..."')
        print('  Bash:               export ANTHROPIC_API_KEY="sk-ant-..."')
        print()
        sys.exit(1)

    try:
        from commercial_reasoning_engine.llm.claude_adapter import ClaudeAdapter
        adapter = ClaudeAdapter(api_key=api_key)
    except ImportError as e:
        print(f"ERROR importando ClaudeAdapter: {e}")
        sys.exit(1)

    cases = sorted(MSG2_DIR.glob('*.md'))
    print(f"\nSprint Beta 3 — LLM Quality — {len(cases)} casos MSG2\n")

    results = []
    for i, p in enumerate(cases, 1):
        print(f"  [{i:02d}/{len(cases)}] Corriendo: {p.stem[:40]}", end=' ', flush=True)
        r = run_case(p, adapter)
        if r is None:
            print("SKIP")
            continue
        results.append(r)
        print(f"-> {r['category']}  ({r['time_s']}s)")

    if not results:
        print("Sin resultados.")
        return

    # ── Table ──────────────────────────────────────────────────────────────────

    print()
    print("=" * 100)
    print(f"{'#':<4}{'Nombre':<26}{'Senior':<10}{'Strategy':<14}{'Rev':<6}{'Qs':<5}{'Categoria':<20}{'Issues'}")
    print("-" * 100)
    for i, r in enumerate(results, 1):
        rev = 'OK' if r['reviewer_approved'] else 'FAIL'
        issues_str = '; '.join(r['issues'])[:45] if r['issues'] else '-'
        print(f"{i:<4}{r['name'][:26]:<26}{r['seniority']:<10}{r['motor_strategy']:<14}"
              f"{rev:<6}{r['q_count']:<5}{r['category']:<20}{issues_str}")
    print("=" * 100)

    # ── Messages preview ───────────────────────────────────────────────────────

    print("\n--- MENSAJES NO-PASS ---")
    for r in results:
        if r['category'] == 'PASS':
            continue
        print(f"\n[{r['name']}] -> {r['category']}")
        print(f"  Problemas: {r['issues']}")
        print(f"  GENERADO:\n{r['generated'][:400]}")
        print(f"  FLORENCIA:\n{r['florencia'][:300]}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────────

    cat_counts = defaultdict(int)
    issue_types = defaultdict(int)
    for r in results:
        cat_counts[r['category']] += 1
        for issue in r['issues']:
            first_word = issue.split(':')[0].strip()
            issue_types[first_word] += 1

    passes = cat_counts['PASS']
    total  = len(results)
    top_issues = sorted(issue_types.items(), key=lambda x: -x[1])[:3]

    if passes == total:
        rec_target = "Ninguno. Listo para produccion."
    elif issue_types.get('Perspectiva', 0) + issue_types.get('Blocklist', 0) > 2:
        rec_target = "Context Builder — el prompt esta enviando mal el punto de partida al LLM."
    elif issue_types.get('Faltan', 0) > 2:
        rec_target = "Context Builder — elementos obligatorios no estan llegando al prompt."
    elif issue_types.get('Reviewer', 0) > 0:
        rec_target = "Reviewer — esta rechazando mensajes correctos (falso positivo de la barrera)."
    else:
        rec_target = "Prompt — ajustes finos de tono, estructura o vocabulario."

    # session_summary.md
    summary = f"""# Session Summary — CRE Beta

**Fecha:** 2026-07-09
**Estado:** SPRINT BETA 3 COMPLETADO

---

## SPRINT BETA 3 — LLM Quality

Casos analizados: {total} (MSG2)

PASS: {cat_counts['PASS']}
MINOR DIFFERENCE: {cat_counts['MINOR DIFFERENCE']}
FALSE POSITIVE: {cat_counts['FALSE POSITIVE']}
FALSE NEGATIVE: {cat_counts['FALSE NEGATIVE']}

Hallazgos principales:
{chr(10).join(f'- {k}: {v} casos' for k, v in top_issues) if top_issues else '- Sin patrones criticos'}

Recomendacion:
Cambios necesarios en: {rec_target}

---

Sprint Beta 1 (MSG2 decision): 15/15 PASS
Sprint Beta 2 (SEG1 decision): 6/8 PASS + 2 EXPECTED FAIL
Sprint Beta 3 (LLM quality):   {passes}/{total} PASS

Proximos pasos:
- Aplicar correcciones al modulo identificado
- Re-correr Sprint Beta 3 para validar mejora
- Comandos: python cre_sprint_beta3.py (requiere ANTHROPIC_API_KEY)
"""
    (BASE / "commercial_reasoning_engine" / "docs" / "session_summary.md").write_text(summary, encoding='utf-8')

    # Print final box
    print()
    print("=" * 60)
    print("  SPRINT BETA 3 — LLM QUALITY")
    print("=" * 60)
    print(f"  Casos analizados    : {total}")
    print()
    print(f"  PASS                : {cat_counts['PASS']}")
    print(f"  MINOR DIFFERENCE    : {cat_counts['MINOR DIFFERENCE']}")
    print(f"  FALSE POSITIVE      : {cat_counts['FALSE POSITIVE']}")
    print(f"  FALSE NEGATIVE      : {cat_counts['FALSE NEGATIVE']}")
    print()
    print("  Hallazgos principales:")
    if top_issues:
        for k, v in top_issues:
            print(f"    {k}: {v} casos")
    else:
        print("    Sin patrones criticos.")
    print()
    print(f"  Corregir en: {rec_target}")
    print("=" * 60)
    print(f"\n  Session summary: commercial_reasoning_engine/docs/session_summary.md")

if __name__ == '__main__':
    main()
