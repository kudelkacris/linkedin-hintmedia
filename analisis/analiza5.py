# -*- coding: utf-8 -*-
import os, re, json, collections, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
MESES = ["junio", "julio", "agosto", "septiembre"]

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()

# ---------- A. TIPO DE ANGULO DE APERTURA ----------
print("=" * 78)
print("A. TIPO DE SENAL / ANGULO USADO EN EL MSG1")
print("=" * 78)
ANG = [
 ('Publicacion / post reciente', r'tu post|publicacion|publicaste|compartiste|lo que compartis|tu articulo|newsletter|compartes'),
 ('Frase textual del prospecto', r'"|«|dijiste|tu frase|escribiste|la idea de que'),
 ('Logro / hito concreto', r'lanzaron|abrieron|cerraron|lograron|creciste|expansion|aniversario|premio|certificac|nuevo rol|asumiste'),
 ('Trayectoria / experiencia', r'anos en|trayectoria|carrera|experiencia de|recorrido|desde hace'),
 ('Cargo / empresa (mas debil)', r'como (gerente|director|responsable|lider)|en tu rol|tu puesto'),
]
for lab, pat in ANG:
    g = [x for x in rows if re.search(pat, norm(x.get('msg1_txt', '')))]
    if len(g) < 20:
        continue
    n = len(g)
    print("%-32s n=%4d  resp %5.1f%%  doss %5.1f%%" % (lab, n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))

# ---------- B. PREGUNTA vs AFIRMACION EN EL CIERRE ----------
print()
print("=" * 78)
print("B. TIPO DE CIERRE (CTA) DEL MSG1")
print("=" * 78)
CTA = [
 ('"Vale la pena que te cuente..."', r'vale la pena que te cuente'),
 ('"Tenia una consulta"', r'tenia una consulta|queria hacerte una consulta|una consulta'),
 ('"Me podrias ayudar"', r'me podrias ayudar|podrias ayudarme|si me podes ayudar'),
 ('Ofrece dossier directo', r'dossier'),
 ('Propone reunion/llamada', r'llamada|reunion|conversacion|charla de'),
]
for lab, pat in CTA:
    g = [x for x in rows if re.search(pat, norm(x.get('msg1_txt', '')))]
    if len(g) < 15:
        continue
    n = len(g)
    print("%-34s n=%4d  resp %5.1f%%  doss %5.1f%%" % (lab, n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))

# ---------- C. CURIOSIDADES ----------
print()
print("=" * 78)
print("C. CURIOSIDADES")
print("=" * 78)
resp_rows = [x for x in rows if x['resp1'] and x['resp_txt'].strip()]
print("1) Respuestas mas largas (mejores charlas):")
for x in sorted(resp_rows, key=lambda y: -y['len_resp'])[:8]:
    print("   %-26s %-11s %5d ch  doss=%s  %s" % (x['nombre'][:26], x['mes'], x['len_resp'], 'SI' if x['dossier'] else 'no', x['sector'][:22]))

print()
print("2) Ratio respuesta segun si el .md tiene analisis HIGH confidence:")
for c in ('HIGH', 'MEDIUM', 'LOW'):
    g = [x for x in rows if x['confidence'] == c]
    if len(g) > 20:
        print("   %-7s n=%4d  resp %5.1f%%  doss %5.1f%%" % (c, len(g), sum(x['resp1'] for x in g)/len(g)*100, sum(x['dossier'] for x in g)/len(g)*100))

print()
print("3) Mujeres vs hombres: quien da mail/telefono y quien propone reunion")
for g_ in ('Mujer', 'Hombre'):
    sub = [x for x in resp_rows if x['genero'] == g_]
    if not sub:
        continue
    mail = sum(1 for x in sub if re.search(r'@\w+\.\w|celular|whatsapp', norm(x['resp_txt'])))
    reu = sum(1 for x in sub if re.search(r'reunion|llamada|call|agendar|meet', norm(x['resp_txt'])))
    print("   %-7s respuestas=%3d  da contacto %4.1f%%  propone reunion %4.1f%%" % (g_, len(sub), mail/len(sub)*100, reu/len(sub)*100))

print()
print("4) Sectores donde el dossier convierte mejor (n>=20):")
agg = collections.defaultdict(lambda: [0, 0])
for x in rows:
    agg[x['sector']][0] += 1
    agg[x['sector']][1] += x['dossier']
for k, (n, d) in sorted(agg.items(), key=lambda kv: -kv[1][1]/max(kv[1][0], 1)):
    if n >= 20 and k != 'N/D':
        print("   %-30s n=%3d  doss %5.1f%%" % (k[:30], n, d/n*100))

print()
print("5) Volumen mensual vs calidad (la hipotesis del escalado):")
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    n = len(r)
    w = [x['msg1_words'] for x in r if x.get('msg1_words')]
    hi = sum(1 for x in r if x['confidence'] == 'HIGH')
    print("   %-11s contactos=%3d  palabras MSG1=%5.1f  analisis HIGH=%4.1f%%  resp=%5.1f%%" % (
        mes, n, sum(w)/len(w) if w else 0, hi/n*100, sum(x['resp1'] for x in r)/n*100))

print()
print("6) Cuantos contactos NUNCA recibieron segundo toque:")
solo1 = [x for x in rows if not x['msg2'] and not x['seg1'] and not x['msg3']]
print("   %d de %d (%.1f%%) se quedaron en un solo mensaje" % (len(solo1), len(rows), len(solo1)/len(rows)*100))
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    s = [x for x in r if not x['msg2'] and not x['seg1'] and not x['msg3']]
    print("      %-11s %3d/%3d = %5.1f%%" % (mes, len(s), len(r), len(s)/len(r)*100))

print()
print("7) Respondieron pero NUNCA recibieron MSG2 (leads quemados):")
quem = [x for x in rows if x['resp1'] and not x['msg2']]
print("   %d leads respondieron y quedaron sin seguimiento" % len(quem))
for mes in MESES:
    q = [x for x in quem if x['mes'] == mes]
    r = [x for x in rows if x['mes'] == mes and x['resp1']]
    if r:
        print("      %-11s %3d de %3d respuestas = %5.1f%% desperdiciadas" % (mes, len(q), len(r), len(q)/len(r)*100))

print()
print("8) Paises con mejor dossier rate (n>=25):")
agg = collections.defaultdict(lambda: [0, 0, 0])
for x in rows:
    a = agg[x['pais']]
    a[0] += 1; a[1] += x['dossier']; a[2] += x['resp1']
for k, (n, d, rp) in sorted(agg.items(), key=lambda kv: -kv[1][1]/max(kv[1][0], 1)):
    if n >= 25 and k != 'N/D':
        print("   %-18s n=%3d  resp %5.1f%%  doss %5.1f%%" % (k, n, rp/n*100, d/n*100))
