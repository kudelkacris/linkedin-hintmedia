# -*- coding: utf-8 -*-
import os, re, json, collections, unicodedata, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
MESES = ["junio", "julio", "agosto", "septiembre"]
MNUM = {"junio": 6, "julio": 7, "agosto": 8, "septiembre": 9}

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()

def fdate(x):
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2})', x['fecha'] or '')
    if m:
        try:
            return datetime.date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except Exception:
            pass
    return datetime.date(2026, MNUM[x['mes']], 15)

for x in rows:
    x['d'] = fdate(x).isoformat()

# ---------- A. ANTES / DESPUES del cambio de metodologia 20/08 ----------
print("=" * 78)
print("A. CAMBIO METODOLOGIA MSG1 (20/08/26: 3 burbujas, Hint dentro del MSG1)")
print("=" * 78)
CUT = datetime.date(2026, 8, 20)
pre = [x for x in rows if datetime.date.fromisoformat(x['d']) < CUT]
pos = [x for x in rows if datetime.date.fromisoformat(x['d']) >= CUT]
for lab, g in (("ANTES 20/08", pre), ("DESDE 20/08", pos)):
    n = len(g) or 1
    wl = [x.get('msg1_words', 0) for x in g if x.get('msg1_words')]
    print("%-12s n=%4d | resp %5.1f%% | MSG2 %5.1f%% | doss %5.1f%% | SEG1 %5.1f%% | palabras MSG1 media %.0f" % (
        lab, len(g), sum(x['resp1'] for x in g)/n*100, sum(x['msg2'] for x in g)/n*100,
        sum(x['dossier'] for x in g)/n*100, sum(x['seg1'] for x in g)/n*100,
        (sum(wl)/len(wl)) if wl else 0))

# ---------- B. HINT MENCIONADO EN MSG1 ----------
print()
print("=" * 78)
print("B. MENCIONAR HINT DENTRO DEL MSG1 - impacto")
print("=" * 78)
for x in rows:
    x['hint_en_msg1'] = bool(re.search(r'hint media|en hint', norm(x.get('msg1_txt', ''))))
    x['cta_dossier_msg1'] = bool(re.search(r'dossier', norm(x.get('msg1_txt', ''))))
for lab, key in (("Hint EN el MSG1", 'hint_en_msg1'), ("CTA dossier EN el MSG1", 'cta_dossier_msg1')):
    print("\n" + lab + ":")
    for val in (False, True):
        g = [x for x in rows if x.get(key) == val and x.get('msg1_words')]
        if len(g) < 20:
            continue
        n = len(g)
        print("   %-3s n=%4d  resp %5.1f%%  doss %5.1f%%  (palabras %.0f)" % (
            "SI" if val else "NO", n, sum(x['resp1'] for x in g)/n*100,
            sum(x['dossier'] for x in g)/n*100, sum(x['msg1_words'] for x in g)/n))
# control por mes (para separar efecto tiempo)
print("\n   Control - solo agosto+septiembre:")
sub = [x for x in rows if x['mes'] in ('agosto', 'septiembre') and x.get('msg1_words')]
for val in (False, True):
    g = [x for x in sub if x['hint_en_msg1'] == val]
    if len(g) < 20:
        continue
    n = len(g)
    print("      Hint en MSG1 %-3s n=%4d  resp %5.1f%%  doss %5.1f%%" % (
        "SI" if val else "NO", n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))

# ---------- C. LONGITUD controlada por mes ----------
print()
print("=" * 78)
print("C. LONGITUD MSG1 vs RESPUESTA, CONTROLADO POR MES (aisla el efecto real)")
print("=" * 78)
print("%-11s %-12s %5s %8s %8s" % ("mes", "bucket", "n", "resp%", "doss%"))
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes and x.get('msg1_words')]
    for b, lo, hi in (('corto <75', 0, 75), ('medio 75-100', 75, 100), ('largo 100+', 100, 9999)):
        g = [x for x in r if lo <= x['msg1_words'] < hi]
        if len(g) < 12:
            continue
        n = len(g)
        print("%-11s %-12s %5d %7.1f%% %7.1f%%" % (mes, b, n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))

# ---------- D. EMBUDO POST-DOSSIER: el agujero ----------
print()
print("=" * 78)
print("D. EMBUDO POST-DOSSIER (donde se pierde el dinero)")
print("=" * 78)
doss = [x for x in rows if x['dossier']]
print("Total dossiers (todos los meses): %d" % len(doss))
con_seg = [x for x in doss if x['seg1']]
print("  con SEG1 de follow-up : %3d (%.1f%%)" % (len(con_seg), len(con_seg)/len(doss)*100))
print("  SIN SEG1 (abandonados): %3d (%.1f%%)" % (len(doss)-len(con_seg), (len(doss)-len(con_seg))/len(doss)*100))
print("  con reunion           : %3d (%.1f%%)" % (sum(x['reunion'] for x in doss), sum(x['reunion'] for x in doss)/len(doss)*100))
print()
print("Reunion segun si hubo SEG1:")
for lab, g in (("CON SEG1", con_seg), ("SIN SEG1", [x for x in doss if not x['seg1']])):
    if g:
        print("   %-9s n=%3d -> reuniones %d (%.1f%%)" % (lab, len(g), sum(x['reunion'] for x in g), sum(x['reunion'] for x in g)/len(g)*100))
print()
print("Dossiers por mes y su follow-up:")
for mes in MESES:
    d = [x for x in rows if x['mes'] == mes and x['dossier']]
    if d:
        print("   %-11s doss=%3d  con SEG1=%3d (%5.1f%%)  reuniones=%d" % (
            mes, len(d), sum(x['seg1'] for x in d), sum(x['seg1'] for x in d)/len(d)*100, sum(x['reunion'] for x in d)))

# ---------- E. TODAS LAS REUNIONES ----------
print()
print("=" * 78)
print("E. LAS REUNIONES - quienes fueron")
print("=" * 78)
for x in rows:
    if x['reunion']:
        print("   %-11s %-28s %-22s %-20s %s" % (x['mes'], x['nombre'][:28], (x['cargo'] or '')[:22], x['sector'][:20], x['pais']))

# ---------- F. VELOCIDAD: cuantos dias desde MSG1 hasta hoy para septiembre ----------
print()
print("=" * 78)
print("F. MADUREZ DE LA COHORTE SEPTIEMBRE (sesgo de medicion)")
print("=" * 78)
hoy = datetime.date(2026, 9, 20)
sep = [x for x in rows if x['mes'] == 'septiembre']
for lo, hi, lab in ((14, 999, '15+ dias'), (7, 14, '7-14 dias'), (0, 7, '<7 dias')):
    g = [x for x in sep if lo <= (hoy - datetime.date.fromisoformat(x['d'])).days < hi]
    if len(g) < 10:
        continue
    n = len(g)
    print("   %-10s n=%3d  resp %5.1f%%  doss %5.1f%%" % (lab, n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))
print()
print("   Comparacion justa: cohorte con 15+ dias de maduracion, todos los meses")
for mes in MESES:
    g = [x for x in rows if x['mes'] == mes and (hoy - datetime.date.fromisoformat(x['d'])).days >= 15]
    if len(g) < 20:
        continue
    n = len(g)
    print("   %-11s n=%4d  resp %5.1f%%  doss %5.1f%%" % (mes, n, sum(x['resp1'] for x in g)/n*100, sum(x['dossier'] for x in g)/n*100))

json.dump(rows, open(os.path.join(HERE, 'rows.json'), 'w', encoding='utf-8'), ensure_ascii=False)
