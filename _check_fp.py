# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from pathlib import Path
from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.llm.adapter import LLMAdapter
from commercial_reasoning_engine.run import run

class DryRun(LLMAdapter):
    def _call(self, p): return "[DRY RUN]"

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

for fname in ['007_diana-kuhlmann.md', '008_pedro-vita.md']:
    p = Path(f'commercial_reasoning_engine/benchmark/seg1/{fname}')
    text = p.read_text(encoding='utf-8', errors='replace')
    orig = text[text.find('## Conversacion original'):]
    seniority = meta(text, 'Seniority')
    sector = meta(text, 'Sector')
    bench_eng = meta(text, 'Engagement')
    name_m = re.search(r'^# Benchmark.*?-- (.+)$', text, re.MULTILINE)
    name = name_m.group(1).strip() if name_m else fname

    blocks = []
    for s in ['MSG1', 'Respuesta MSG1', 'MSG2', 'Respuesta MSG2']:
        c = sec(orig, s)
        if c: blocks.append(c)
    conv = '\n\n'.join(blocks)

    conversation = parse(conv, prospect_name=name)
    result = run(conversation, adapter=DryRun(), prospect_data={
        'stage': '3', 'sector': sector,
        'cargo_seniority': seniority, 'days_since_dossier': 5
    })

    r1 = sec(orig, 'Respuesta MSG1')
    r2 = sec(orig, 'Respuesta MSG2')

    print(f'{name}')
    print(f'  Bench engagement : {bench_eng}')
    print(f'  Motor engagement : {result.analysis.engagement.value}')
    print(f'  Motor temperature: {result.analysis.temperature.value}')
    print(f'  Motor strategy   : {result.strategy_cl.strategy.value}')
    print(f'  Propose meeting  : {result.decision.propose_meeting}')
    print(f'  RespMSG1: {r1[:120]}')
    print(f'  RespMSG2: {r2[:120]}')
    print()
