# -*- coding: utf-8 -*-
"""
cre_sprint_beta3.py — Sprint Beta 3: Context Export

Corre el pipeline completo (sin API) sobre los 15 casos MSG2.
Exporta el LLMContext de cada caso como prompt .txt listo para pegar en cualquier LLM.

Sin dependencias de pago. Sin ANTHROPIC_API_KEY.

Uso:
    python cre_sprint_beta3.py

Output:
    sprint_beta3_output/<nombre>.txt   — prompt completo por caso
    sprint_beta3_output/README.txt     — instrucciones para evaluación manual

Flujo:
    1. Correr este script
    2. Abrir cada .txt en sprint_beta3_output/
    3. Pegarlo en Claude Code / ChatGPT / Ollama / el LLM que usés
    4. Copiar la respuesta de vuelta
    5. (futuro) Correr el Reviewer sobre el resultado
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
from commercial_reasoning_engine.llm.context_only_adapter import ContextOnlyAdapter

BASE        = Path(__file__).parent
MSG2_DIR    = BASE / "commercial_reasoning_engine" / "benchmark" / "msg2"
OUTPUT_DIR  = BASE / "sprint_beta3_output"

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
    lines = [l[1:].strip() if l.strip().startswith('>') else l for l in raw.splitlines()]
    lines = [l for l in lines if l.strip() not in ('---', '***', '___')]
    return '\n'.join(lines).strip()

# ── Runner ────────────────────────────────────────────────────────────────────

def run_case(p, adapter):
    t0 = time.time()
    text = p.read_text(encoding='utf-8', errors='replace')
    orig = text[text.find('## Conversacion original'):]

    seniority = meta(text, 'Seniority')
    sector    = meta(text, 'Sector')
    name_m    = re.search(r'—\s*([^—\n]+)\s*$', text, re.MULTILINE)
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

    return {
        'name': name,
        'seniority': seniority,
        'sector': sector,
        'motor_strategy': result.strategy_cl.strategy.value if result.strategy_cl else '?',
        'motor_engagement': result.analysis.engagement.value if result.analysis.engagement else '?',
        'context_exported': result.context is not None,
        'florencia': florencia_msg2,
        'blocked': result.blocked,
        'block_reason': result.block_reason,
        'time_s': elapsed,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    adapter = ContextOnlyAdapter(output_dir=OUTPUT_DIR)

    cases = sorted(MSG2_DIR.glob('*.md'))
    print(f"\nSprint Beta 3 — Context Export — {len(cases)} casos MSG2\n")
    print(f"  Output: {OUTPUT_DIR}\n")

    results = []
    for i, p in enumerate(cases, 1):
        print(f"  [{i:02d}/{len(cases)}] {p.stem[:40]}", end=' ', flush=True)
        r = run_case(p, adapter)
        if r is None:
            print("SKIP")
            continue
        results.append(r)
        status = "OK" if r['context_exported'] and not r['blocked'] else "BLOCKED"
        print(f"-> {status}  ({r['time_s']}s)")

    # ── Tabla ─────────────────────────────────────────────────────────────────

    print()
    print("=" * 90)
    print(f"{'#':<4}{'Nombre':<30}{'Senior':<12}{'Engagement':<12}{'Strategy':<16}{'Contexto'}")
    print("-" * 90)
    for i, r in enumerate(results, 1):
        ctx = "exportado" if r['context_exported'] and not r['blocked'] else f"BLOCKED: {r['block_reason'] or ''}"
        print(f"{i:<4}{r['name'][:30]:<30}{r['seniority']:<12}{r['motor_engagement']:<12}"
              f"{r['motor_strategy']:<16}{ctx}")
    print("=" * 90)

    exported = sum(1 for r in results if r['context_exported'] and not r['blocked'])
    blocked  = sum(1 for r in results if r['blocked'])

    # ── README para evaluación manual ─────────────────────────────────────────

    readme = f"""Sprint Beta 3 — Evaluacion manual de calidad LLM
=================================================

Fecha: {time.strftime('%Y-%m-%d')}
Casos: {len(results)}
Exportados: {exported}
Bloqueados: {blocked}

Como evaluar
------------

1. Abrir cada archivo .txt en esta carpeta.
2. Copiar TODO el contenido (template + contexto) y pegarlo en el LLM que estes usando:
   - Claude Code: pegar directo en el chat
   - ChatGPT: pegar en una nueva conversacion
   - Ollama: ollama run <modelo> < <archivo>.txt
3. Copiar la respuesta del LLM.
4. Evaluar con la rubrica:

Rubrica (puntuacion /10 por criterio):
  - Apertura (B1): conecta con la respuesta del prospecto?
  - Rapport: usa palabras del prospecto, iguala tono emocional?
  - Naturalidad: suena humano o parece un template?
  - Fluidez: las burbujas transicionan sin saltos?
  - Curiosidad: da ganas de seguir leyendo?
  - Personalizacion: podria ser para cualquier otro prospecto?
  - Pregunta final: es especifica o generica?
  - Parece Florencia?: nivel de proximidad al estilo real

Total: /80

Casos en esta carpeta:
"""
    for i, r in enumerate(results, 1):
        status = "OK" if not r['blocked'] else f"BLOQUEADO ({r['block_reason']})"
        readme += f"  {i:02d}. {r['name']} [{r['seniority']} / {r['sector']}] — {status}\n"

    (OUTPUT_DIR / "README.txt").write_text(readme, encoding='utf-8')

    # ── session_summary.md ────────────────────────────────────────────────────

    summary = f"""# Session Summary — CRE Beta

**Fecha:** {time.strftime('%Y-%m-%d')}
**Estado:** SPRINT BETA 3 — CONTEXTOS EXPORTADOS

---

## SPRINT BETA 3

Arquitectura: LLM-agnostica. Sin API obligatoria.
Adapters disponibles: ContextOnly, OpenAICompatible, Claude (opcional).

Casos analizados: {len(results)}
Contextos exportados: {exported}
Bloqueados: {blocked}

Output: sprint_beta3_output/ ({exported} archivos .txt)

Proximos pasos:
- Pegar cada .txt en cualquier LLM (Claude Code / ChatGPT / Ollama)
- Evaluar con rubrica manual (/10 por criterio x 8 criterios)
- Identificar patron de fallos (Prompt / Context Builder / Strategy Builder)

---

Sprint Beta 1 (MSG2 decision): 15/15 PASS
Sprint Beta 2 (SEG1 decision): 6/8 PASS + 2 EXPECTED FAIL
Sprint Beta 3 (LLM context):   {exported}/{len(results)} contextos exportados
"""
    (BASE / "commercial_reasoning_engine" / "docs" / "session_summary.md").write_text(summary, encoding='utf-8')

    # ── Resumen final ─────────────────────────────────────────────────────────

    print()
    print("=" * 55)
    print("  SPRINT BETA 3 — CONTEXT EXPORT")
    print("=" * 55)
    print(f"  Casos analizados    : {len(results)}")
    print(f"  Contextos exportados: {exported}")
    print(f"  Bloqueados          : {blocked}")
    print()
    print(f"  Archivos en: {OUTPUT_DIR}")
    print(f"  Instrucciones en: {OUTPUT_DIR / 'README.txt'}")
    print()
    print("  Proximos pasos:")
    print("  1. Pegar cada .txt en Claude Code / ChatGPT / Ollama")
    print("  2. Evaluar con rubrica manual")
    print("  3. Identificar patron de fallos -> modulo a corregir")
    print("=" * 55)
    print(f"\n  session_summary.md actualizado.")


if __name__ == '__main__':
    main()
