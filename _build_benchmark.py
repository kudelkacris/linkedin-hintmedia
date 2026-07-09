# -*- coding: utf-8 -*-
"""
_build_benchmark.py
Analiza todas las conversaciones, clasifica, selecciona y construye benchmark/.
"""
import sys, io, re, random, json, shutil
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
CONV_DIRS = [BASE / "conversaciones" / "julio", BASE / "conversaciones" / "junio"]
BENCH_DIR = BASE / "commercial_reasoning_engine" / "benchmark"

# ── Helpers ───────────────────────────────────────────────────────────────────

def meta(text, field):
    m = re.search(rf'\*\*{field}:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else ''

def has_section(text, name):
    return bool(re.search(rf'^##\s+{re.escape(name)}\s*$', text, re.MULTILINE))

def section_content(text, name):
    m = re.search(rf'^##\s+{re.escape(name)}\s*$', text, re.MULTILINE)
    if not m:
        return ''
    start = m.end()
    nxt = re.search(r'^##\s+', text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    raw = text[start:end].strip()
    # strip blockquote
    lines = [l[1:].strip() if l.strip().startswith('>') else l for l in raw.splitlines()]
    return '\n'.join(lines).strip()

def seniority(cargo):
    c = cargo.lower()
    if any(x in c for x in ['ceo','chief executive','presidente','fundador','founder']):
        return 'CEO'
    if any(x in c for x in ['director','vp ','vice president','vicepresidente']):
        return 'DIRECTOR'
    if any(x in c for x in ['manager','gerente','jefe','head of']):
        return 'MANAGER'
    if any(x in c for x in ['specialist','especialista','analyst','analista','coordinator']):
        return 'SPECIALIST'
    return 'OTHER'

def sector_short(sector):
    s = sector.lower()
    if any(x in s for x in ['energ','gas','petro','infra','esg','minería','mineria']):
        return 'Energia'
    if any(x in s for x in ['retail','e-commerce','marketplace','consumo']):
        return 'Retail'
    if any(x in s for x in ['tech','tecnolog','software','digital','saas']):
        return 'Tech'
    if any(x in s for x in ['salud','health','farma','medical','clinica']):
        return 'Salud'
    if any(x in s for x in ['educac','univers','formac']):
        return 'Educacion'
    if any(x in s for x in ['marketing','agencia','publicidad','advertising','branding','comunicac']):
        return 'Marketing'
    if any(x in s for x in ['finanzas','seguros','banking','banca','financial']):
        return 'Finanzas'
    if any(x in s for x in ['turismo','hotel','hospit','viaje']):
        return 'Turismo'
    if any(x in s for x in ['consultor','legal','juridic']):
        return 'Consultoria'
    if any(x in s for x in ['inmob','real estate','construccion','construc']):
        return 'Inmobiliaria'
    return 'Otro'

def classify(text, estado, sections):
    e = estado.lower()

    # CERRADA / no response / discarded
    if any(x in e for x in ['cerrada','descartad','no interesad','referido','retirado']):
        return 'WAIT'

    # SEG2 — explicit
    if 'seg2' in e:
        return 'SEG2'

    # SEG1 — dossier sent, waiting
    if any(x in e for x in ['dossier enviado','seg1']):
        return 'SEG1'

    # Reunion — dossier was sent and meeting was booked
    if any(x in e for x in ['reunion','reuni','stage 6']):
        return 'SEG1'  # motor at the point before reunion = post-dossier

    # MSG2 — msg1 was sent and prospect responded
    if 'msg2 enviado' in e:
        return 'MSG2'
    if has_section(text, 'Respuesta MSG1') and not has_section(text, 'MSG2'):
        return 'MSG2'
    if has_section(text, 'Respuesta MSG1'):
        return 'MSG2'

    return None  # skip — no usable state

def engagement_score(text, estado):
    "Rough engagement from response length and keywords."
    resp = section_content(text, 'Respuesta MSG1')
    if not resp:
        return 'NONE'
    words = len(resp.split())
    resp_l = resp.lower()
    if any(x in resp_l for x in ['me interesa','con gusto','me encanta','hablemos','cuéntame','cuentame','perfecto','excelente','qué interesante','que interesante']):
        return 'HIGH'
    if words > 30:
        return 'MEDIUM'
    if words < 8 or any(x in resp_l for x in ['ok','claro','dale','👍','buenas']):
        return 'LOW'
    return 'MEDIUM'

def complexity_score(text, cat):
    "Rough complexity: multiple objections, redirections, mixed signals."
    has_objection = bool(re.search(r'ya tenemos|trabaj[ao] con|no necesi|no es el momento|no es lo que', text, re.IGNORECASE))
    has_question = bool(re.search(r'\?', section_content(text, 'Respuesta MSG1')))
    has_redirect = bool(re.search(r'contacta[r]? a|pasarte el contacto|habla con', text, re.IGNORECASE))
    has_msg2_resp = has_section(text, 'Respuesta MSG2')
    score = sum([has_objection, has_question, has_redirect, has_msg2_resp])
    if score >= 2:
        return 'HIGH'
    if score == 1:
        return 'MEDIUM'
    return 'LOW'

# ── Load all ──────────────────────────────────────────────────────────────────

records = []
errors = []

for d in CONV_DIRS:
    for p in sorted(d.glob('*.md')):
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
            name_m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
            name = name_m.group(1).strip() if name_m else p.stem
            cargo = meta(text, 'Cargo')
            sector = meta(text, 'Sector')
            estado = meta(text, 'Estado')

            has_r1 = has_section(text, 'Respuesta MSG1')
            if not has_r1:
                continue  # no prospect response at all — skip

            cat = classify(text, estado, None)
            if cat is None:
                continue

            eng = engagement_score(text, estado)
            sen = seniority(cargo)
            sec = sector_short(sector)
            cmp = complexity_score(text, cat)

            records.append({
                'path': p,
                'mes': p.parent.name,
                'name': name,
                'cargo': cargo[:80],
                'sector': sec,
                'seniority': sen,
                'estado': estado[:80],
                'category': cat,
                'engagement': eng,
                'complexity': cmp,
                'has_msg2_resp': has_section(text, 'Respuesta MSG2'),
                'has_objection': bool(re.search(r'ya tenemos|trabaj[ao] con|no necesi|no es el momento', text, re.IGNORECASE)),
            })
        except Exception as ex:
            errors.append((p, str(ex)))

# ── Stats ──────────────────────────────────────────────────────────────────────

by_cat = defaultdict(list)
for r in records:
    by_cat[r['category']].append(r)

print(f"\nTotal clasificados: {len(records)}")
for cat, lst in sorted(by_cat.items()):
    print(f"  {cat:<12}: {len(lst)}")
print(f"  Errores    : {len(errors)}")

# ── Selection ─────────────────────────────────────────────────────────────────

TARGETS = {'MSG2': 15, 'SEG1': 8, 'SEG2': 3, 'WAIT': 2, 'RECOVERY': 2}
# RECOVERY = high complexity cases from MSG2/SEG1 with objection or redirect
# EDGE = high complexity + unusual sector

def diverse_sample(pool, n, keys=('seniority','sector','engagement','complexity')):
    """Greedy diversity sampling: maximize unique combinations."""
    if len(pool) <= n:
        return pool[:]
    selected = []
    seen = defaultdict(set)
    # Sort by complexity desc, engagement desc first
    order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'NONE': 3}
    pool_s = sorted(pool, key=lambda r: (order.get(r['complexity'],3), order.get(r['engagement'],3)))

    for r in pool_s:
        if len(selected) >= n:
            break
        sig = tuple(r.get(k,'?') for k in keys)
        if sig not in [tuple(s.get(k,'?') for k in keys) for s in selected]:
            selected.append(r)
        elif len(selected) < n // 2:
            selected.append(r)

    # fill remainder randomly
    remaining = [r for r in pool_s if r not in selected]
    random.seed(99)
    random.shuffle(remaining)
    while len(selected) < n and remaining:
        selected.append(remaining.pop(0))

    return selected

selected = {}
used_paths = set()

def pick(pool, n):
    """Sample n from pool excluding already-used paths, then mark as used."""
    available = [r for r in pool if r['path'] not in used_paths]
    result = diverse_sample(available, n)
    for r in result:
        used_paths.add(r['path'])
    return result

# Priority order: special categories first so they get unique cases

# SEG2 — explicit + high complexity SEG1
seg2_pool = by_cat.get('SEG2', []) + [r for r in by_cat['SEG1'] if r['complexity'] == 'HIGH']
selected['SEG2'] = pick(seg2_pool, 3)

# RECOVERY — objections or redirects
recovery_pool = [r for r in by_cat['MSG2'] + by_cat['SEG1'] if r['has_objection'] or r['has_msg2_resp']]
selected['RECOVERY'] = pick(recovery_pool, 2)

# EDGE — unusual sector + high complexity
edge_pool = [r for r in records if r['sector'] in ('Educacion','Salud','Inmobiliaria','Consultoria','Otro') and r['complexity'] != 'LOW']
selected['EDGE'] = pick(edge_pool, 2)

# WAIT
selected['WAIT'] = pick(by_cat['WAIT'], 2)

# MSG2 — most common, pick after specials
selected['MSG2'] = pick(by_cat['MSG2'], 15)

# SEG1 — after MSG2
selected['SEG1'] = pick(by_cat['SEG1'], 8)

# ── Build benchmark/ ──────────────────────────────────────────────────────────

BENCH_DIR.mkdir(parents=True, exist_ok=True)
for cat in ('MSG2','SEG1','SEG2','WAIT','RECOVERY','EDGE'):
    (BENCH_DIR / cat.lower()).mkdir(exist_ok=True)

manifest = []
counters = defaultdict(int)

def write_bench_case(r, cat, idx):
    text = r['path'].read_text(encoding='utf-8', errors='replace')
    slug = r['path'].stem

    # What the motor should decide
    if cat == 'MSG2':
        expected_action = 'MSG2'
        expected_stage = '1'
        days_dossier = ''
    elif cat in ('SEG1','RECOVERY'):
        expected_action = 'SEG1'
        expected_stage = '3'
        days_dossier = '5'
    elif cat == 'SEG2':
        expected_action = 'SEG2'
        expected_stage = '4'
        days_dossier = '10'
    elif cat == 'WAIT':
        expected_action = 'WAIT'
        expected_stage = '2'
        days_dossier = ''
    elif cat == 'EDGE':
        expected_action = '?'
        expected_stage = '1'
        days_dossier = ''
    else:
        expected_action = '?'
        expected_stage = '1'
        days_dossier = ''

    fname = f"{idx:03d}_{slug}.md"
    dest = BENCH_DIR / cat.lower() / fname

    # Build benchmark case file
    days_line = f"\n**Days dossier:** {days_dossier}" if days_dossier else ''
    content = f"""# Benchmark — {cat} — {r['name']}

**Fuente:** conversaciones/{r['mes']}/{r['path'].name}
**Categoria:** {cat}
**Seniority:** {r['seniority']}
**Sector:** {r['sector']}
**Engagement:** {r['engagement']}
**Complexity:** {r['complexity']}
**Estado:** {r['estado']}
**Expected action:** {expected_action}
**Expected stage:** {expected_stage}{days_line}

---

## Conversacion original

{text.strip()}

---

## Evaluacion CRE

**Resultado CRE:**
- Action:
- Strategy:
- Engagement:
- Reviewer:

**Categoria benchmark:** <!-- PASS / FALSE POSITIVE / FALSE NEGATIVE / EXPECTED FAIL -->

**Modulo raiz:** <!-- si hay error -->

**Tiempo identificacion:** <!-- min -->

**Diagnostico:**

---

## Criterio humano

<!-- Que escribio Florencia realmente? Pegar MSG2 o SEG1 real. -->

"""
    dest.write_text(content, encoding='utf-8')
    return fname

for cat, lst in selected.items():
    for i, r in enumerate(lst, 1):
        fname = write_bench_case(r, cat, i)
        manifest.append({
            'file': f"{cat.lower()}/{fname}",
            'name': r['name'],
            'category': cat,
            'seniority': r['seniority'],
            'sector': r['sector'],
            'engagement': r['engagement'],
            'complexity': r['complexity'],
        })

# Write manifest
manifest_path = BENCH_DIR / 'manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

# ── Diversity check ───────────────────────────────────────────────────────────

all_senior = set(r['seniority'] for r in manifest)
all_sector = set(r['sector'] for r in manifest)
all_eng = set(r['engagement'] for r in manifest)
diversity_ok = len(all_senior) >= 3 and len(all_sector) >= 4 and len(all_eng) >= 2

# ── session_summary.md ────────────────────────────────────────────────────────

total_selected = len(manifest)
counts = {cat: sum(1 for m in manifest if m['category'] == cat) for cat in ('MSG2','SEG1','SEG2','WAIT','RECOVERY','EDGE')}

summary = f"""# Session Summary — CRE Beta

**Fecha:** 2026-07-09
**Estado:** BENCHMARK PREPARADO

---

## BETA PREPARADA

Conversaciones analizadas: {len(records)}

Seleccionadas:
- MSG2: {counts.get('MSG2',0)}
- SEG1: {counts.get('SEG1',0)}
- SEG2: {counts.get('SEG2',0)}
- WAIT: {counts.get('WAIT',0)}
- RECOVERY: {counts.get('RECOVERY',0)}
- EDGE: {counts.get('EDGE',0)}
- TOTAL: {total_selected}

Diversidad: {'OK' if diversity_ok else 'NO'}
- Seniority: {sorted(all_senior)}
- Sector: {sorted(all_sector)}
- Engagement: {sorted(all_eng)}

Problemas encontrados:
- {len(errors)} archivos con error de lectura (codificacion)
- SEG2 escaso en dataset: completado con SEG1 de alta complejidad
- RECOVERY armado desde MSG2/SEG1 con objeciones (no hay categoria propia en .md)

Proximo paso recomendado:
Correr cre_batch_test.py sobre benchmark/ y llenar la columna
'Resultado CRE' en cada .md. Empezar por MSG2 (15 casos).

---

Archivos: commercial_reasoning_engine/benchmark/
Manifest: commercial_reasoning_engine/benchmark/manifest.json
"""

summary_path = BASE / "commercial_reasoning_engine" / "docs" / "session_summary.md"
summary_path.write_text(summary, encoding='utf-8')
print(summary)
print(f"\nBenchmark en: {BENCH_DIR}")
print(f"Summary en  : {summary_path}")
