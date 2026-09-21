# -*- coding: utf-8 -*-
import os, re, json, collections, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
MESES = ["junio", "julio", "agosto", "septiembre"]

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()

# ---------- A. SESGO DE MADUREZ: cohorte por quincena ----------
print("=" * 78)
print("A. CONTROL DE SESGO - cohorte primera quincena (dia 1-15) de cada mes")
print("=" * 78)
print("%-11s %6s %8s %8s %8s" % ("mes", "n", "resp%", "doss%", "msg2%"))
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    q1 = []
    for x in r:
        m = re.match(r'(\d{1,2})/', x['fecha'] or '')
        if m and int(m.group(1)) <= 15:
            q1.append(x)
    if len(q1) < 10:
        print("%-11s %6d  (muestra chica)" % (mes, len(q1)))
        continue
    n = len(q1)
    print("%-11s %6d %7.1f%% %7.1f%% %7.1f%%" % (mes, n, sum(x['resp1'] for x in q1)/n*100,
          sum(x['dossier'] for x in q1)/n*100, sum(x['msg2'] for x in q1)/n*100))

# ---------- B. LONGITUD DEL MSG1 vs conversion ----------
print()
print("=" * 78)
print("B. LONGITUD DEL MSG1 vs CONVERSION")
print("=" * 78)
def get_msg1(mes, fn):
    p = os.path.join(BASE, 'conversaciones', mes, fn)
    try:
        t = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ""
    out, cur = [], None
    for line in t.split('\n'):
        if line.startswith('## '):
            cur = norm(line[3:])
        elif cur and cur.startswith('msg1'):
            out.append(line)
    return '\n'.join(out).strip()

buckets = collections.defaultdict(lambda: dict(n=0, resp=0, doss=0))
lens_by_mes = collections.defaultdict(list)
for x in rows:
    m1 = get_msg1(x['mes'], x['file'])
    w = len(re.findall(r'\w+', m1))
    x['msg1_words'] = w
    x['msg1_txt'] = m1[:2500]
    if w == 0:
        continue
    lens_by_mes[x['mes']].append(w)
    b = '0-60' if w < 60 else '60-90' if w < 90 else '90-120' if w < 120 else '120-160' if w < 160 else '160+'
    d = buckets[b]; d['n'] += 1; d['resp'] += x['resp1']; d['doss'] += x['dossier']
for b in ['0-60', '60-90', '90-120', '120-160', '160+']:
    d = buckets[b]
    if d['n'] >= 15:
        print("%-9s palabras  n=%4d  resp %5.1f%%  doss %5.1f%%" % (b, d['n'], d['resp']/d['n']*100, d['doss']/d['n']*100))
print()
print("Largo medio MSG1 por mes:")
for mes in MESES:
    L = lens_by_mes[mes]
    if L:
        L2 = sorted(L)
        print("   %-11s media %5.1f palabras   mediana %5.1f   n=%d" % (mes, sum(L)/len(L), L2[len(L2)//2], len(L)))

# ---------- C. QUE CONTESTARON: clasificacion de respuestas ----------
print()
print("=" * 78)
print("C. QUE CONTESTARON - clasificacion de las respuestas reales")
print("=" * 78)
PAT = [
 ('Interes explicito / pide info', r'me interesa|interesante|contame|cuentame|cuéntame|dale|me gustaria saber|quiero saber|envia|enviame|mandame|pasame|manda el dossier|con gusto|encantad|claro que si|perfecto|buenisimo|genial'),
 ('Pide dossier / material', r'dossier|material|propuesta|portafolio|informacion|brochure|presentacion'),
 ('Da mail / telefono', r'@\w+\.\w|correo|mail:|celular|whatsapp|telefono|\+\d{2,}'),
 ('Deriva a otra persona', r'hablar con|deriv|contacta a|escribile a|la persona|encargad|responsable de|mi socio|mi colega|area de'),
 ('Objecion: ya tenemos agencia/equipo', r'ya tenemos|ya contamos|tenemos agencia|equipo interno|agencia propia|in.house|ya trabajamos con'),
 ('Objecion: no es el momento / timing', r'mas adelante|por ahora no|en este momento|no es el momento|proximo ano|el ano que viene|mas adelante|retomar|despues de'),
 ('Objecion: no soy yo / no es mi area', r'no soy|no es mi area|no manejo|no me encargo|no llevo|no corresponde|no estoy a cargo'),
 ('Rechazo directo', r'no gracias|no, gracias|no estoy interesad|no me interesa|no estamos buscando|no necesitamos'),
 ('Solo cortesia / brush-off', r'^gracias|muchas gracias|suerte con|exitos|saludos cordiales|un gusto'),
 ('Pregunta que hacemos / que venden', r'que hacen|a que se dedic|que ofrec|de que se trata|que me quieres vender|que venden|en que consiste'),
 ('Propone reunion / call', r'reunion|reunirnos|llamada|call|agendar|meet|zoom|coordinar una|calendly'),
 ('Respuesta larga y elaborada (>400 ch)', None),
]
resp_rows = [x for x in rows if x['resp1'] and x['resp_txt'].strip()]
print("Respuestas con texto capturado: %d" % len(resp_rows))
cls = collections.Counter()
cls_doss = collections.Counter()
for x in resp_rows:
    t = norm(x['resp_txt'])
    for lab, pat in PAT:
        hit = (len(x['resp_txt']) > 400) if pat is None else bool(re.search(pat, t))
        if hit:
            cls[lab] += 1
            if x['dossier']:
                cls_doss[lab] += 1
print()
print("%-42s %6s %7s %8s" % ("tipo de respuesta", "n", "doss", "doss%"))
for lab, _ in PAT:
    n = cls[lab]
    if n:
        print("%-42s %6d %7d %7.1f%%" % (lab, n, cls_doss[lab], cls_doss[lab]/n*100))

# ---------- D. objeciones por mes ----------
print()
print("=" * 78)
print("D. MIX DE RESPUESTA POR MES (%% de las respuestas del mes)")
print("=" * 78)
keylabs = ['Interes explicito / pide info', 'Objecion: ya tenemos agencia/equipo', 'Objecion: no es el momento / timing',
           'Objecion: no soy yo / no es mi area', 'Rechazo directo', 'Solo cortesia / brush-off',
           'Pregunta que hacemos / que venden', 'Propone reunion / call', 'Deriva a otra persona']
hdr = "%-38s" % "tipo"
for mes in MESES:
    hdr += "%11s" % mes[:9]
print(hdr)
for lab in keylabs:
    pat = dict(PAT)[lab]
    line = "%-38s" % lab[:38]
    for mes in MESES:
        sub = [x for x in resp_rows if x['mes'] == mes]
        if not sub:
            line += "%11s" % "-"
            continue
        c = sum(1 for x in sub if re.search(pat, norm(x['resp_txt'])))
        line += "%10.1f%%" % (c/len(sub)*100)
    print(line)

# ---------- E. palabras mas usadas por prospectos ----------
print()
print("=" * 78)
print("E. LO QUE MAS DICEN (palabras de contenido en respuestas)")
print("=" * 78)
STOP = set("""el la los las un una unos unas de del al a en y o que se su sus es son por para con no si me te le lo mi tu
como mas pero ya muy sobre este esta estos estas ese esa eso todo toda todos todas hay ser estar tiene tengo puede
puedo hola buenas gracias florencia saludos cordial bien dia tarde noche usted ustedes nos nuestro nuestra yo el
tambien cuando donde quien cual desde hasta entre sin sino porque pues asi aqui alli ahora antes despues siempre
nunca solo mismo otro otra otros otras cada tan tanto poco mucha mucho muchos muchas cosa cosas hacer hace hecho
vamos vaya voy va van estoy estamos estan era eran fue fueron han he ha hemos habia sera seria puedes podemos""".split())
w = collections.Counter()
for x in resp_rows:
    for t in re.findall(r'[a-zñáéíóú]{4,}', norm(x['resp_txt'])):
        if t not in STOP:
            w[t] += 1
print(", ".join("%s(%d)" % (k, v) for k, v in w.most_common(45)))

json.dump(rows, open(os.path.join(HERE, 'rows.json'), 'w', encoding='utf-8'), ensure_ascii=False)
