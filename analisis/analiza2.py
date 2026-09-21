# -*- coding: utf-8 -*-
import os, re, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
hist = json.load(open(os.path.join(BASE, 'historial.json'), encoding='utf-8'))
MESES = ["junio", "julio", "agosto", "septiembre"]
MN = {"06": "junio", "07": "julio", "08": "agosto", "09": "septiembre"}

# ---------- 1. historial por mes (denominador real de envios) ----------
print("=" * 78)
print("1. HISTORIAL.JSON POR MES (denominador real)")
print("=" * 78)
hm = collections.defaultdict(list)
for e in hist:
    d = str(e.get('date') or e.get('fecha') or '')
    m = re.match(r'(\d{1,2})/(\d{2})/(\d{2})', d)
    if m and m.group(2) in MN:
        hm[MN[m.group(2)]].append(e)
print("%-11s %6s %8s %8s %8s %8s %8s" % ("mes", "total", "st>=2", "st>=3", "st>=4", "st6", "noInt"))
hstats = {}
for mes in MESES:
    r = hm[mes]
    n = len(r)
    def st(e):
        try:
            return int(str(e.get('stage', 0)).strip() or 0)
        except Exception:
            return 0
    s2 = sum(1 for e in r if st(e) >= 2); s3 = sum(1 for e in r if st(e) >= 3)
    s4 = sum(1 for e in r if st(e) >= 4); s6 = sum(1 for e in r if st(e) >= 6)
    ni = sum(1 for e in r if e.get('noInterest'))
    hstats[mes] = dict(total=n, s2=s2, s3=s3, s4=s4, s6=s6, ni=ni)
    if n:
        print("%-11s %6d %8d %8d %8d %8d %8d   (st2 %.1f%% | st3 %.1f%%)" % (mes, n, s2, s3, s4, s6, ni, s2/n*100, s3/n*100))

# ---------- 2. embudo por mes desde .md ----------
print()
print("=" * 78)
print("2. EMBUDO POR MES (archivos .md)")
print("=" * 78)
funnel = {}
print("%-11s %5s %7s %7s %7s %7s %7s %6s" % ("mes", "MSG1", "resp", "MSG2", "doss", "SEG1", "cierre", "noInt"))
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    n = len(r)
    f = dict(n=n, resp=sum(x['resp1'] for x in r), msg2=sum(x['msg2'] for x in r),
             doss=sum(x['dossier'] for x in r), seg1=sum(x['seg1'] for x in r),
             seg2=sum(x['seg2'] for x in r), cierre=sum(x['cierre'] for x in r),
             noint=sum(x['nointeres'] for x in r), reunion=sum(x['reunion'] for x in r),
             resp2=sum(x['resp2'] for x in r))
    funnel[mes] = f
    print("%-11s %5d %7d %7d %7d %7d %7d %6d" % (mes, n, f['resp'], f['msg2'], f['doss'], f['seg1'], f['cierre'], f['noint']))
print()
print("TASAS %:")
print("%-11s %8s %8s %10s %10s %10s" % ("mes", "resp/MSG1", "MSG2/resp", "doss/MSG1", "doss/resp", "SEG1/doss"))
for mes in MESES:
    f = funnel[mes]; n = f['n'] or 1; rp = f['resp'] or 1; do = f['doss'] or 1
    print("%-11s %8.1f %8.1f %10.1f %10.1f %10.1f" % (mes, f['resp']/n*100, f['msg2']/rp*100, f['doss']/n*100, f['doss']/rp*100, f['seg1']/do*100))

# ---------- 3. cortes demograficos ----------
def corte(campo, titulo, minn=8, topn=14):
    print()
    print("=" * 78)
    print(titulo)
    print("=" * 78)
    agg = collections.defaultdict(lambda: dict(n=0, resp=0, doss=0, noint=0, reu=0))
    for x in rows:
        a = agg[x[campo]]
        a['n'] += 1; a['resp'] += x['resp1']; a['doss'] += x['dossier']
        a['noint'] += x['nointeres']; a['reu'] += x['reunion']
    items = sorted(agg.items(), key=lambda kv: -kv[1]['n'])
    print("%-30s %5s %7s %8s %7s %8s %5s" % (campo, "n", "resp", "resp%", "doss", "doss%", "reu"))
    for k, a in items[:topn]:
        if a['n'] < minn:
            continue
        print("%-30s %5d %7d %7.1f%% %7d %7.1f%% %5d" % (str(k)[:30], a['n'], a['resp'], a['resp']/a['n']*100, a['doss'], a['doss']/a['n']*100, a['reu']))
    return agg

g_agg = corte('genero', "3. POR GENERO", minn=1)
s_agg = corte('seniority', "4. POR SENIORITY", minn=5, topn=15)
sec_agg = corte('sector', "5. POR SECTOR", minn=10, topn=18)
p_agg = corte('pais', "6. POR PAIS", minn=10, topn=16)
c_agg = corte('confidence', "7. POR CONFIDENCE DEL ANALISIS", minn=5)

# ---------- 4. genero x mes ----------
print()
print("=" * 78)
print("8. GENERO x MES (mix y conversion)")
print("=" * 78)
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    line = mes.ljust(11)
    for g in ("Mujer", "Hombre"):
        sub = [x for x in r if x['genero'] == g]
        if sub:
            line += " | %s n=%3d (%4.1f%% mix) resp %4.1f%% doss %4.1f%%" % (
                g[:3], len(sub), len(sub)/len(r)*100,
                sum(x['resp1'] for x in sub)/len(sub)*100, sum(x['dossier'] for x in sub)/len(sub)*100)
    print(line)

# ---------- 5. sector x mes (top) ----------
print()
print("=" * 78)
print("9. TOP SECTORES POR MES (n>=6)")
print("=" * 78)
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    cnt = collections.Counter(x['sector'] for x in r)
    top = [k for k, v in cnt.most_common(6) if v >= 6]
    print("\n" + mes.upper())
    for k in top:
        sub = [x for x in r if x['sector'] == k]
        print("   %-28s n=%3d resp %5.1f%%  doss %5.1f%%" % (k[:28], len(sub),
              sum(x['resp1'] for x in sub)/len(sub)*100, sum(x['dossier'] for x in sub)/len(sub)*100))

json.dump(dict(funnel=funnel, hstats=hstats), open(os.path.join(HERE, 'stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
