# -*- coding: utf-8 -*-
"""Prueba ANCLA contra Haiku real: extrae el SYSTEM de index.html y genera mensajes."""
import io, os, re, json, urllib.request, unicodedata

BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"

# --- API key
key = ''
for l in io.open(os.path.join(BASE, '.env.local'), encoding='utf-8', errors='replace'):
    if l.startswith('ANTHROPIC_API_KEY'):
        key = l.split('=', 1)[1].strip()
assert key.startswith('sk-ant-')

# --- extraer el SYSTEM del index.html
h = io.open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
i = h.find('const SYSTEM = `')
j = h.find('`;', i)
SYSTEM = h[i + len('const SYSTEM = `'):j]
print("SYSTEM extraido: %d caracteres" % len(SYSTEM))
assert 'SISTEMA ANCLA' in SYSTEM and 'LANGUAGE BANK' in SYSTEM

# --- extraer el template del prompt de usuario
k = h.find('MSG1_B1: (burbuja 1: seguir SISTEMA ANCLA')
tail = h[k:h.find('`;', k)]
print("template de salida: %d caracteres" % len(tail))

PERFILES = [
    dict(nombre="Maleka Carrasco Casagrande", pais="Peru", tipo="DECISOR",
         perfil="""Subgerente de Comercializacion | Energia Electrica & Gas | Desarrollo de Negocios B2B.
Empresa del sector energia en Peru. En su descripcion de perfil escribe que busca
"generar impacto a traves de soluciones innovadoras en la transicion energetica".
Publicaciones recientes: comparte contenido sobre transicion energetica y contratos de suministro."""),
    dict(nombre="Flavio Melian", pais="Argentina", tipo="NO_DECISOR",
         perfil="""Project Manager | Gerenciamiento de Proyectos en Oil&Gas y Mineria.
Publicacion reciente: una reflexion sobre complejidad e incertidumbre en proyectos, donde dice que
sabemos teoricamente como deberia ser la gestion pero "volvemos a lo conocido" en la implementacion.
La publicacion queda sin una conclusion cerrada."""),
    dict(nombre="Ana Rosa Marquez", pais="Mexico", tipo="DECISOR",
         perfil="""Directora General de una constructora en Mexico.
Publicacion reciente: anuncio de la entrega de un conjunto habitacional. En el texto nombra
uno por uno a los cinco jefes de obra y agradece al equipo de topografia antes de mencionar el proyecto."""),
]

TPL = """Analiza este perfil de LinkedIn y genera el MSG1 siguiendo el SISTEMA ANCLA.

PERFIL:
NOMBRE DEL PROSPECTO: %s
%s

TIPO_CONTACTO: %s
PAIS: %s

Responde SOLO con el bloque de salida, sin analisis previo:
%s"""


def call(system, prompt):
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001", "max_tokens": 3000,
        "system": system, "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages', data=body,
        headers={'x-api-key': key, 'anthropic-version': '2023-06-01',
                 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d['content'][0]['text'], d.get('usage', {})


def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()


MOLDE = r'no es lo que (normalmente|suele|tipicamente|la mayoria)|la mayoria (arma|lo centra|comunica|hace|de)|no es lo mas comun|mas honesto que'
HUMO = r'credibilidad|presencia|solucion|construimos|resolvemos|escale|complejo|narrativa legible|hacer legible|capa de comunicacion'

total = 0
for p in PERFILES:
    print("\n" + "=" * 74)
    print(p['nombre'], "|", p['pais'], "|", p['tipo'])
    print("=" * 74)
    try:
        out, us = call(SYSTEM, TPL % (p['nombre'], p['perfil'], p['tipo'], p['pais'], tail))
    except Exception as e:
        print("ERROR:", e)
        continue
    # aislar SOLO las burbujas del mensaje, sin el analisis previo
    msg = ''
    for m in re.finditer(r'MSG1_B[123]:(.*)', out):
        msg += m.group(1).strip() + chr(10)
    cierre = re.search(r'CIERRE_USADO:\s*([ABC])', out)
    print('--- MENSAJE GENERADO ---')
    print(msg.strip() if msg.strip() else '(no se encontraron burbujas)')
    print('--- CIERRE_USADO:', cierre.group(1) if cierre else 'FALTA')
    n = norm(msg)
    b1 = re.search(r'MSG1_B1:(.*)', out)
    words = len(re.findall(r"\w+", msg))
    print("\n--- VERIFICACION AUTOMATICA ---")
    checks = [
        ("saluda con 'gracias por conectar'", 'gracias por conectar' in n),
        ("usa 'me llamo la atencion'", 'llamo la atencion' in n),
        ("SIN molde comparativo", not re.search(MOLDE, n)),
        ("SIN vocabulario de humo", not re.search(HUMO, n)),
        ("SIN 'vale la pena que te cuente'", 'vale la pena que te cuente' not in n),
        ("SIN guion largo", chr(8212) not in msg),
        ("SIN signos de apertura", not re.search(r'[\u00bf\u00a1]', out)),
        ("SIN 'mientras'", ' mientras ' not in n),
        ("tiene CIERRE_USADO", bool(cierre)),
        ("menciona cliente real", bool(re.search(r'tgs|transener|sullair|tassaroli|agora|destiny|spain collection|libra|royal english|grupo one', n))),
    ]
    ok = sum(1 for _, v in checks if v)
    total += ok
    for lab, v in checks:
        print("   [%s] %s" % ("OK" if v else "XX", lab))
    print("   palabras aprox del mensaje: %d" % words)
    print("   score: %d/%d   tokens: in=%s out=%s" % (ok, len(checks), us.get('input_tokens'), us.get('output_tokens')))

print("\n" + "=" * 74)
print("SCORE TOTAL: %d/%d" % (total, len(PERFILES) * 10))
