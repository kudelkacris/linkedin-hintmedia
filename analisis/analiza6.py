# -*- coding: utf-8 -*-
"""Mide si el CTA 'tenia una consulta' genera pushback o desconfianza."""
import os, re, json, unicodedata, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()

CONSULTA = r'tenia una consulta|queria hacerte una consulta|una consulta|me podrias ayudar|si me podes ayudar'
VALEPENA = r'vale la pena que te cuente'

grp_c = [x for x in rows if re.search(CONSULTA, norm(x.get('msg1_txt', '')))]
grp_v = [x for x in rows if re.search(VALEPENA, norm(x.get('msg1_txt', '')))]

# senales de desconfianza / pushback en la respuesta
PUSH = {
 'Pregunta cual es la consulta': r'que consulta|cual es la consulta|cual es tu consulta|de que se trata|dime tu consulta|cual seria|que necesitas saber|en que te puedo ayudar|que duda|dime que duda',
 'Sospecha de venta': r'que me quieres vender|me estas vendiendo|esto es una venta|que vendes|no me interesa comprar|si es para vender|parece un pitch|esto es publicidad',
 'Reproche / molestia': r'no me interesa|no gracias|por favor no|spam|dejame de|no escribas',
 'Rechazo directo': r'^no\b|no gracias|no estoy interesad|no me interesa',
}

print("=" * 76)
print("PUSHBACK SEGUN EL CTA DEL MSG1")
print("=" * 76)
print("%-34s %8s %8s" % ("", '"tenia una consulta"', '"vale la pena"'))
print("%-34s %8d %14d" % ("contactos", len(grp_c), len(grp_v)))
rc = [x for x in grp_c if x['resp1'] and x['resp_txt'].strip()]
rv = [x for x in grp_v if x['resp1'] and x['resp_txt'].strip()]
print("%-34s %8d %14d" % ("respuestas con texto", len(rc), len(rv)))
print()
for lab, pat in PUSH.items():
    a = sum(1 for x in rc if re.search(pat, norm(x['resp_txt'])))
    b = sum(1 for x in rv if re.search(pat, norm(x['resp_txt'])))
    pa = a / len(rc) * 100 if rc else 0
    pb = b / len(rv) * 100 if rv else 0
    print("%-34s %4d (%4.1f%%) %6d (%4.1f%%)" % (lab, a, pa, b, pb))

print()
print("=" * 76)
print("LOS QUE PREGUNTARON 'QUE CONSULTA' - que paso despues")
print("=" * 76)
pat = PUSH['Pregunta cual es la consulta']
askers = [x for x in rc if re.search(pat, norm(x['resp_txt']))]
print("Total que pidieron la consulta: %d de %d respuestas (%.1f%%)" % (len(askers), len(rc), len(askers)/len(rc)*100 if rc else 0))
print("  de esos, recibieron MSG2 : %d" % sum(x['msg2'] for x in askers))
print("  de esos, pidieron dossier: %d (%.1f%%)" % (sum(x['dossier'] for x in askers),
      sum(x['dossier'] for x in askers)/len(askers)*100 if askers else 0))
print("  de esos, se cerraron sin interes: %d" % sum(x['nointeres'] for x in askers))
print()
print("Comparacion tasa de dossier:")
print("  Pidieron 'que consulta' : %.1f%%" % (sum(x['dossier'] for x in askers)/len(askers)*100 if askers else 0))
print("  Resto de respuestas     : %.1f%%" % (sum(x['dossier'] for x in rc if x not in askers)/max(len(rc)-len(askers),1)*100))
print()
print("Ejemplos textuales (primeros 10):")
for x in askers[:10]:
    t = re.sub(r'\s+', ' ', x['resp_txt'])[:120]
    print("   [%s] %-22s doss=%s | %s" % (x['mes'][:4], x['nombre'][:22], 'SI' if x['dossier'] else 'no', t))

print()
print("=" * 76)
print("SOSPECHA DE VENTA - donde aparece realmente")
print("=" * 76)
pat = PUSH['Sospecha de venta']
for lab, grp in (('"tenia una consulta"', rc), ('"vale la pena que te cuente"', rv)):
    hits = [x for x in grp if re.search(pat, norm(x['resp_txt']))]
    print("%-32s %d de %d respuestas (%.1f%%)" % (lab, len(hits), len(grp), len(hits)/len(grp)*100 if grp else 0))
    for x in hits[:4]:
        t = re.sub(r'\s+', ' ', x['resp_txt'])[:110]
        print("      %-20s | %s" % (x['nombre'][:20], t))

print()
print("=" * 76)
print("RESULTADO FINAL DE CADA GRUPO")
print("=" * 76)
for lab, g in (('"tenia una consulta"', grp_c), ('"vale la pena que te cuente"', grp_v)):
    n = len(g)
    print("%-32s n=%3d | resp %5.1f%% | MSG2 %5.1f%% | doss %5.1f%% | cerrado sin interes %5.1f%%" % (
        lab, n, sum(x['resp1'] for x in g)/n*100, sum(x['msg2'] for x in g)/n*100,
        sum(x['dossier'] for x in g)/n*100, sum(x['nointeres'] for x in g)/n*100))
