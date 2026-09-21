# -*- coding: utf-8 -*-
"""Construye el HINT LANGUAGE BANK desde las 1.102 conversaciones reales."""
import os, re, json, collections, unicodedata, math

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))


def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()


def full(x):
    p = os.path.join(BASE, 'conversaciones', x['mes'], x['file'])
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def sec(txt, pat):
    """texto de la primera seccion ## que matchea"""
    out, cur, taken = [], None, False
    for line in txt.split('\n'):
        if line.startswith('## '):
            cur = norm(line[3:])
            if taken and out:
                break
        elif cur and re.search(pat, cur):
            out.append(re.sub(r'^> ?', '', line))
            taken = True
    return '\n'.join(out).strip()


MAIL = r'[\w\.\-]+@[\w\.\-]+\.\w{2,}'

# ---------- 1. clasificar por resultado verificado ----------
for x in rows:
    t = full(x)
    x['_msg1'] = sec(t, r'^msg1')
    x['_msg2'] = sec(t, r'^msg2')
    x['_resp'] = x['resp_txt']
    zonas = x['resp_txt'] + ' ' + x['notas']
    x['dio_contacto'] = bool(re.search(MAIL, zonas) or re.search(r'celular|whatsapp|telefono|movil', norm(zonas)))
    x['charla'] = x['len_resp'] > 500 or (x['resp2'] and x['msg3'])
    if x['reunion']:
        x['outcome'] = 'REUNION'
    elif x['dio_contacto']:
        x['outcome'] = 'CONTACTO'
    elif x['charla']:
        x['outcome'] = 'CHARLA'
    elif x['dossier']:
        x['outcome'] = 'DOSSIER'
    elif x['resp1']:
        x['outcome'] = 'RESPONDIO_MURIO'
    else:
        x['outcome'] = 'SIN_RESPUESTA'

cnt = collections.Counter(x['outcome'] for x in rows)
print("CLASIFICACION POR RESULTADO VERIFICADO")
for k in ['REUNION', 'CONTACTO', 'CHARLA', 'DOSSIER', 'RESPONDIO_MURIO', 'SIN_RESPUESTA']:
    print("   %-18s %4d" % (k, cnt[k]))

GANADORES = {'REUNION', 'CONTACTO', 'CHARLA'}
win = [x for x in rows if x['outcome'] in GANADORES and x['_msg1']]
lose = [x for x in rows if x['outcome'] == 'SIN_RESPUESTA' and x['_msg1']]
print("\n   mensajes ganadores con MSG1: %d | perdedores: %d" % (len(win), len(lose)))

# ---------- 2. vocabulario diferencial (log-odds con prior) ----------
def toks(s):
    return re.findall(r"[a-zñáéíóúü]{3,}", norm(s))

cw, cl = collections.Counter(), collections.Counter()
for x in win:
    cw.update(set(toks(x['_msg1'])))
for x in lose:
    cl.update(set(toks(x['_msg1'])))
STOP = set("""para con que los las del una uno por como más pero este esta esos esas donde cuando cual quien sobre
entre desde hasta sin sino porque pues así aquí ahora antes después siempre nunca solo mismo otro otra cada tan
tanto poco mucha mucho cosa cosas hacer hace hecho vamos estoy estamos están era eran fue fueron han hemos había
será sería puede pueden puedo buenas hola gracias que qué tus sus les nos van ser estar tiene tengo esa ese eso
todo toda todos todas hay muy también según tras ante bajo cabe""".split())

NW, NL = len(win), len(lose)
rank = []
for w in set(list(cw) + list(cl)):
    if w in STOP or len(w) < 4:
        continue
    a, b = cw[w], cl[w]
    if a + b < 12:
        continue
    pw = (a + 0.5) / (NW + 1)
    pl = (b + 0.5) / (NL + 1)
    lo = math.log(pw / (1 - pw)) - math.log(pl / (1 - pl))
    rank.append((lo, w, a, round(a / NW * 100, 1), b, round(b / NL * 100, 1)))
rank.sort(reverse=True)
print("\nPALABRAS QUE APARECEN EN LOS QUE FUNCIONARON (top 22)")
print("   %-18s %6s %8s %8s" % ("palabra", "gana%", "pierde%", "ratio"))
for lo, w, a, pa, b, pb in rank[:22]:
    print("   %-18s %5.1f%% %7.1f%%   %+.2f" % (w, pa, pb, lo))
print("\nPALABRAS DE LOS QUE MURIERON (top 22)")
for lo, w, a, pa, b, pb in rank[-22:][::-1]:
    print("   %-18s %5.1f%% %7.1f%%   %+.2f" % (w, pa, pb, lo))

# ---------- 3. ejemplos reales para el banco ----------
def clean(s, lim=700):
    s = re.sub(r'^> ?', '', s or '', flags=re.M)
    s = re.sub(r'\n{2,}', '\n', s).strip()
    return s[:lim]

bank = {'REUNION': [], 'CONTACTO': [], 'CHARLA': [], 'RESPONDIO_MURIO': []}
for k in bank:
    sub = [x for x in rows if x['outcome'] == k and x['_msg1'] and len(x['_msg1']) > 60]
    sub.sort(key=lambda y: -(y['len_resp']))
    for x in sub:
        bank[k].append(dict(nombre=x['nombre'], mes=x['mes'], sector=x['sector'], pais=x['pais'],
                            cargo=(x['cargo'] or '')[:70], msg1=clean(x['_msg1']),
                            msg2=clean(x['_msg2'], 800), resp=clean(x['_resp'], 500),
                            palabras=x.get('msg1_words', 0)))

json.dump(dict(bank=bank, vocab_win=[r[1] for r in rank[:40]], vocab_lose=[r[1] for r in rank[-40:]]),
          open(os.path.join(HERE, 'bank_raw.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\nEjemplos capturados: REUNION %d | CONTACTO %d | CHARLA %d | MURIO %d" % (
    len(bank['REUNION']), len(bank['CONTACTO']), len(bank['CHARLA']), len(bank['RESPONDIO_MURIO'])))
