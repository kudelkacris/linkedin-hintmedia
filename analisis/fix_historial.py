# -*- coding: utf-8 -*-
"""Normaliza historial.json: ids faltantes, stage, fechas. No borra ni pisa datos existentes."""
import json, re, unicodedata, shutil, os, datetime, collections

P = r"C:/Users/neces/Desktop/CLAUDE/Linkedin/historial.json"
BAK = P + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

d = json.load(open(P, encoding='utf-8'))
orig = json.dumps(d, ensure_ascii=False, sort_keys=True)
shutil.copy2(P, BAK)
print("backup -> %s" % os.path.basename(BAK))
print("entradas: %d" % len(d))


def slug(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return re.sub(r'^-+|-+$', '', s)[:60]


cambios = collections.Counter()

# ---------- 1. ids faltantes, sin tocar los existentes y sin colisionar ----------
usados = set(e['id'] for e in d if e.get('id'))
for e in d:
    if e.get('id'):
        continue
    base = slug(e.get('name') or e.get('nombre') or '')
    if not base:
        cambios['id_sin_nombre'] += 1
        continue
    cand, n = base, 2
    while cand in usados:
        cand = "%s-%d" % (base, n)
        n += 1
    e['id'] = cand
    usados.add(cand)
    cambios['id_generado'] += 1

# ---------- 2. stage: todo a string numerico ----------
for e in d:
    s = e.get('stage')
    if s is None:
        continue
    if isinstance(s, int):
        e['stage'] = str(s)
        cambios['stage_int_a_str'] += 1
    elif isinstance(s, str) and not s.strip().isdigit():
        # 'CERRADA' u otro texto: convencion del proyecto es stage numerico + noInterest
        e['stage'] = '1'
        e['noInterest'] = True
        cambios['stage_texto_normalizado'] += 1

# ---------- 3. fechas ISO -> dd/mm/aa (formato que usa el programa) ----------
for e in d:
    v = str(e.get('date') or '')
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', v)
    if m:
        y, mo, da = m.groups()
        e['date'] = "%s/%s/%s" % (da, mo, y[2:])
        cambios['fecha_iso_convertida'] += 1
    else:
        m2 = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', v)
        if m2:
            da, mo, y = m2.groups()
            e['date'] = "%02d/%02d/%s" % (int(da), int(mo), y[2:])
            cambios['fecha_4digitos'] += 1

# ---------- verificaciones antes de escribir ----------
assert len(d) == json.loads(orig).__len__(), "cambio la cantidad de entradas"
ids = [e['id'] for e in d if e.get('id')]
assert len(ids) == len(set(ids)), "se generaron ids duplicados"
# ningun campo preexistente se perdio
old = json.loads(orig)
for a, b in zip(old, d):
    for k, v in a.items():
        if k in ('stage', 'date', 'id'):
            continue
        assert b.get(k) == v, "se perdio el campo %s en %s" % (k, a.get('name'))

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print()
for k, v in cambios.most_common():
    print("  %-26s %d" % (k, v))
print()
sin_id = sum(1 for e in d if not e.get('id'))
tipos = collections.Counter(type(e.get('stage')).__name__ for e in d)
malas = sum(1 for e in d if e.get('date') and not re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', str(e['date'])))
print("DESPUES:")
print("  sin id              %d" % sin_id)
print("  tipos de stage      %s" % dict(tipos))
print("  fechas mal formadas %d" % malas)
print("  entradas            %d" % len(d))
