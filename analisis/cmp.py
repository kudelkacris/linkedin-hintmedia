# -*- coding: utf-8 -*-
"""Compara Haiku vs Sonnet con el mismo SYSTEM y los mismos perfiles."""
import io, os, re, json, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
HERE = os.path.dirname(os.path.abspath(__file__))
key = ''
for l in io.open(os.path.join(BASE, '.env.local'), encoding='utf-8', errors='replace'):
    if l.startswith('ANTHROPIC_API_KEY'):
        key = l.split('=', 1)[1].strip()

h = io.open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
i = h.find('const SYSTEM = `')
SYSTEM = h[i + len('const SYSTEM = `'):h.find('`;', i)]
k = h.find('MSG1_B1: (burbuja 1: seguir SISTEMA ANCLA')
TAIL = h[k:h.find('`;', k)]
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))


def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()


def full(x):
    try:
        return io.open(os.path.join(BASE, 'conversaciones', x['mes'], x['file']), encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def campo(t, n):
    m = re.search(r'\*\*' + n + r':\*\*(.*?)(?=\n- \*\*|\n\n|\n---)', t, re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


cands = []
for x in rows:
    if x['mes'] != 'septiembre' or x['resp1']:
        continue
    s = campo(full(x), 'Señal humana')
    if len(s) < 90:
        continue
    x['_senal'] = s[:600]
    cands.append(x)
    if len(cands) >= 10:
        break

# sector -> cliente correcto (para auditar el error de sector)
SEC = {
    'Energia / Oil&Gas': ['tgs', 'transener', 'sullair', 'tassaroli'],
    'Mineria': ['sullair', 'tassaroli'],
    'Construccion / Real Estate': ['sullair'],
    'Industria / Logistica': ['sullair'],
    'Tecnologia / SaaS': ['agora'],
    'Finanzas / Seguros': ['libra', 'agora'],
    'Turismo / Hoteleria': ['destiny', 'spain collection', 'be our guest'],
    'Educacion': ['royal english'],
    'Entretenimiento / Eventos': ['grupo one'],
}
SENIOR = r'ceo|director|gerente general|presidente|founder|fundador|\bvp\b|chief|owner|socio|head of'
TPL = """Analiza este perfil de LinkedIn y genera el MSG1 siguiendo el SISTEMA ANCLA.

PERFIL:
NOMBRE DEL PROSPECTO: %s
CARGO: %s
SECTOR: %s
PAIS: %s
SENAL OBSERVADA:
%s

TIPO_CONTACTO: %s
PAIS: %s

Responde SOLO con el bloque de salida:
%s"""


def gen(args):
    x, model = args
    tipo = 'DECISOR' if re.search(SENIOR, norm(x['cargo'])) else 'NO_DECISOR'
    body = json.dumps({"model": model, "max_tokens": 3000, "system": SYSTEM,
                       "messages": [{"role": "user", "content": TPL % (
                           x['nombre'], x['cargo'][:90], x['sector'], x['pais'],
                           x['_senal'], tipo, x['pais'], TAIL)}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body,
                                 headers={'x-api-key': key, 'anthropic-version': '2023-06-01',
                                          'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            d = json.loads(r.read())
        out = ''.join(b.get('text','') for b in d.get('content',[]) if b.get('type')=='text')
        us = d.get('usage', {})
    except Exception as e:
        return x, model, '', {}, str(e)[:60]
    msg = ''
    for m in re.finditer(r'MSG1_B[123]:(.*)', out):
        msg += m.group(1).strip() + '\n'
    return x, model, msg.strip(), us, ''


MOLDE = r'no es lo que (normalmente|suele|tipicamente|la mayoria)|la mayoria (arma|lo centra|comunica|hace|de)|no es lo mas comun|mas (especifico|honesto) que lo que|no es lo tipico|no es (lo )?comun'
CATALOGO = r'identidad digital,? (management de )?(instagram y )?linkedin,? (y )?videos de lanzamiento'
ALLCLI = r'tgs|transener|sullair|tassaroli|agora|destiny|spain collection|libra|royal english|grupo one|be our guest'

MODELS = [("Haiku 4.5", "claude-haiku-4-5-20251001"), ("Sonnet 4.5", "claude-sonnet-4-5-20250929")]
jobs = [(x, m[1]) for m in MODELS for x in cands]
out = {}
with ThreadPoolExecutor(max_workers=6) as ex:
    for x, model, msg, us, err in ex.map(gen, jobs):
        out.setdefault(model, []).append((x, msg, us, err))

for label, model in MODELS:
    res = out[model]
    print("\n" + "#" * 78)
    print("###  " + label)
    print("#" * 78)
    agg = dict(vacio=0, saludo=0, atencion=0, molde=0, cli_ok=0, cli_mal=0, cli_none=0,
               guion=0, largo_ok=0, catalogo=0, tokin=0, tokout=0)
    for x, msg, us, err in res:
        n = norm(msg)
        w = len(re.findall(r'\w+', msg))
        if not msg.strip():
            agg['vacio'] += 1
            continue
        agg['saludo'] += 'gracias por conectar' in n
        agg['atencion'] += 'llamo la atencion' in n
        agg['molde'] += bool(re.search(MOLDE, n))
        agg['catalogo'] += bool(re.search(CATALOGO, n))
        agg['guion'] += chr(8212) in msg
        agg['largo_ok'] += (60 <= w <= 95)
        ok = SEC.get(x['sector'], [])
        cited = re.findall(ALLCLI, n)
        if not cited:
            agg['cli_none'] += 1
        elif ok and any(c in ok for c in cited):
            agg['cli_ok'] += 1
        elif ok:
            agg['cli_mal'] += 1
        else:
            agg['cli_ok'] += 1
        agg['tokin'] += us.get('input_tokens', 0)
        agg['tokout'] += us.get('output_tokens', 0)
    N = len(res)
    print("   mensajes vacios / error   %d/%d" % (agg['vacio'], N))
    print("   saludo correcto           %d/%d" % (agg['saludo'], N))
    print("   'me llamo la atencion'    %d/%d" % (agg['atencion'], N))
    print("   CON molde (peor)          %d/%d" % (agg['molde'], N))
    print("   CON catalogo repetido     %d/%d" % (agg['catalogo'], N))
    print("   cliente sector CORRECTO   %d/%d" % (agg['cli_ok'], N))
    print("   cliente sector ERRADO     %d/%d" % (agg['cli_mal'], N))
    print("   sin nombrar cliente       %d/%d" % (agg['cli_none'], N))
    print("   guion largo (peor)        %d/%d" % (agg['guion'], N))
    print("   largo 60-95 palabras      %d/%d" % (agg['largo_ok'], N))
    cin = 1.0 if 'haiku' in model else 3.0
    cout = 5.0 if 'haiku' in model else 15.0
    cost = agg['tokin'] / 1e6 * cin + agg['tokout'] / 1e6 * cout
    print("   costo de estos %d msgs     USD %.4f  (proyectado 315/mes: USD %.2f)" % (N, cost, cost / max(N, 1) * 315))

print("\n" + "=" * 78)
print("EJEMPLOS LADO A LADO")
for idx in (0, 3, 6):
    xh, mh, _, _ = out[MODELS[0][1]][idx]
    xs, ms, _, _ = out[MODELS[1][1]][idx]
    print("\n" + "-" * 78)
    print("%s | %s | %s" % (xh['nombre'][:30], xh['sector'][:24], xh['pais']))
    print("-" * 78)
    print("HAIKU:")
    for l in mh.split('\n'):
        print("   " + l)
    print("SONNET:")
    for l in ms.split('\n'):
        print("   " + l)
