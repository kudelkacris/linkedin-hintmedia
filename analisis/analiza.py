# -*- coding: utf-8 -*-
import os, re, json, collections, unicodedata

BASE = r"C:/Users/neces/Desktop/CLAUDE/Linkedin"
HERE = os.path.dirname(os.path.abspath(__file__))
MESES = ["junio", "julio", "agosto", "septiembre"]


def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower().strip()


FEM = set("""maria ana laura carolina silvia paola claudia andrea gabriela alejandra patricia veronica natalia valeria
daniela cecilia lucia sofia martina florencia romina marcela monica adriana viviana sandra karen brenda tatiana diana
susana elena carmen rosa luisa juana clara alicia beatriz nora irene julieta camila agustina micaela melanie soledad
josefina ivanna cristina gloria angela yolanda teresa raquel sara ruth noelia milagros celeste consuelo virginia
constanza rocio jesica jessica estefania mariana antonella antonela leticia lorena vanesa vanessa liliana nadia ximena
maleka katherine johanna ruby luz marta isabel eugenia magdalena valentina emilia catalina francisca javiera macarena
denise debora paula pilar dolores mercedes nicole michelle jennifer karla yessica yesenia alexandra jimena rita edith
erika erica fabiola gisela graciela griselda ingrid ivana karina lidia mabel marisa maritza mayra miriam nancy norma
olga paulina roxana sabrina samanta silvana sonia stella susan tamara vilma wilma yanina zulema kelly nohelia dulce
keylin leandra maricel marilyn analia luciana lucrecia elymar victoria mariemma janette rosario amparo asuncion begona
belen blanca candela carla carmela cintia cinthia dafna delfina eliana elisa esther eva fernanda flavia gimena
guadalupe ileana ines irma jazmin josefa juliana lara leila ludmila maia malena manuela mariel marina marisol mayte
melina mia milena mirta nayla nerina nidia noemi ornella pamela priscila rebeca regina renata rosalia rosana sabina
salome selena serena sol solange tania tracy ursula vera yamila yenny zaira nict katia marisela lissette yunel
josselyn aida maribel maricela""".split())

MASC = set("""juan carlos jose luis miguel pedro pablo diego martin alejandro fernando ricardo roberto eduardo gabriel
daniel javier sergio jorge raul oscar mario antonio francisco manuel rafael victor hector andres gustavo marcelo
sebastian nicolas matias lucas tomas federico ignacio santiago facundo agustin emiliano leandro maximiliano mauricio
gonzalo cristian christian hernan german guillermo gerardo armando alfredo arturo ramiro rodolfo ruben salvador samuel
saul teodoro tobias ulises valentin walter wilson adrian alberto alan aldo alexis alvaro anibal ariel augusto aurelio
benjamin bernardo bruno camilo cesar claudio damian dante dario david demian dylan edgar edgardo edwin elias emanuel
emilio enrique ernesto esteban ezequiel fabian fabio felipe felix fidel gaston gilberto gregorio hugo humberto ivan
jaime jeremias joaquin jonatan jonathan josue julian julio lautaro lorenzo marcos mariano marco mateo mauro maximo
nahuel nestor norberto omar orlando osvaldo patricio paulo rene renzo reynaldo rolando ronaldo sandro santino silvio
simon thiago tiago valentino vicente vladimir yago adolfo alfonso amado anselmo baltazar benito cayetano conrado
cristobal cirilo domingo donato efrain eleuterio eusebio evaristo fausto florencio fortunato froilan gaspar genaro
geronimo godofredo hilario homero horacio isidoro jacinto jacobo jeronimo leonardo leopoldo lisandro macario marcial
melchor nicanor olegario pascual plinio policarpo porfirio primitivo quintin remigio ramon rogelio romeo rosendo rufino
sabino santos segundo serafin severino sixto telmo timoteo tito urbano venancio wenceslao zacarias owen alexsander
alexander bryam eder hans stefan paul yoel erick dan jaye manny freddy wally rigoberto lieven thomas matt mike john
peter nelson alcides chencho zu inigo""".split())


def genero(nombre):
    p = norm(nombre).split()
    if not p:
        return "N/D"
    f = p[0]
    if f in FEM:
        return "Mujer"
    if f in MASC:
        return "Hombre"
    for x in p[:2]:
        if x in FEM:
            return "Mujer"
        if x in MASC:
            return "Hombre"
    if f.endswith('a'):
        return "Mujer"
    if f.endswith(('o', 'r', 'n', 'l', 's', 'e')):
        return "Hombre"
    return "N/D"


def seniority(cargo):
    c = norm(cargo)
    if not c:
        return "N/D"
    if re.search(r'\bceo\b|chief executive|presidente|\bpresident\b|dueno|owner|propietari', c):
        return "CEO/Presidente"
    if re.search(r'founder|fundador|cofundador|co-founder|socio|partner', c):
        return "Founder/Socio"
    if re.search(r'\bcto\b|\bcfo\b|\bcoo\b|\bcmo\b|\bcio\b|chief ', c):
        return "C-Level"
    if re.search(r'vicepresident|\bvp\b|vice president', c):
        return "VP"
    if re.search(r'director|directora|head of|gerente general', c):
        return "Director"
    if re.search(r'gerente|manager|jefe|jefa|\blead\b|leader', c):
        return "Gerente/Manager"
    if re.search(r'coordinador|coordinadora|coordinator|supervisor', c):
        return "Coordinador"
    if re.search(r'especialista|specialist|analista|analyst|consultor|consultant|asesor', c):
        return "Especialista/Consultor"
    if re.search(r'ingenier|arquitect|abogad|medic|profesor|docente|geolog', c):
        return "Profesional tecnico"
    return "Otro"


SECTOR_MAP = [
    (r'miner|mining|litio|lithium|cobre|geolog|extractiv', 'Mineria'),
    (r'energ|oil|gas|petrol|electric|renovabl|solar|eolic|combustib', 'Energia / Oil&Gas'),
    (r'construc|inmobil|real estate|arquitect|infraestructur|obra|hormig|cement|material', 'Construccion / Real Estate'),
    (r'tech|software|saas|\bapp\b|digital|\bit\b|tecnolog|data|\bia\b|inteligencia artificial|platform|startup', 'Tecnologia / SaaS'),
    (r'fintech|financ|banc|seguro|insurance|invers|contab|credit', 'Finanzas / Seguros'),
    (r'salud|health|medic|farmac|pharma|clinic|hospital|odontolog|dental|bienestar|wellness', 'Salud / Farma'),
    (r'educa|universidad|academ|formacion|capacitacion|idioma|school|escuela', 'Educacion'),
    (r'retail|consumo|moda|ecommerce|e-commerce|tienda|comercio|d2c|alimento|food', 'Retail / Consumo'),
    (r'turism|hotel|viaje|travel|hospitality', 'Turismo / Hoteleria'),
    (r'consultor|consulting|asesor|legal|abogac|recursos humanos|\brrhh\b|\bhr\b|talent|people', 'Consultoria / RRHH'),
    (r'marketing|publicid|agencia|comunicac|media|advertis|branding', 'Agencia / Marketing'),
    (r'industri|manufactur|logistic|supply|transport|automotr|maquinar|acero|quimic', 'Industria / Logistica'),
    (r'agro|agricol|campo|ganader|alimentari', 'Agro'),
    (r'gobierno|publico|municipal|estado|\bong\b|fundacion|social|ambiental|\besg\b|sosteni', 'Gobierno / ONG / ESG'),
    (r'entreten|evento|festival|deporte|gaming|igaming|musica|cultur', 'Entretenimiento / Eventos'),
]


def sector_norm(s):
    n = norm(s)
    if not n:
        return "N/D"
    for pat, lab in SECTOR_MAP:
        if re.search(pat, n):
            return lab
    return "Otro"


PAIS_MAP = [
    (r'argentin|buenos aires|cordoba|rosario|mendoza|santa fe|bariloche', 'Argentina'),
    (r'chile|santiago|antofagasta', 'Chile'), (r'colombia|bogot|medell|cali', 'Colombia'),
    (r'mexic|cdmx|guadalajara|monterrey', 'Mexico'), (r'peru|lima', 'Peru'),
    (r'ecuador|quito|guayaquil', 'Ecuador'), (r'espan|spain|madrid|barcelona', 'Espana'),
    (r'uruguay|montevideo', 'Uruguay'), (r'panam', 'Panama'), (r'brasil|brazil|sao paulo', 'Brasil'),
    (r'venezuel|caracas', 'Venezuela'), (r'bolivia|la paz', 'Bolivia'), (r'paraguay|asuncion', 'Paraguay'),
    (r'costa rica', 'Costa Rica'), (r'guatemala', 'Guatemala'), (r'republica dominicana|dominican', 'Rep. Dominicana'),
    (r'estados unidos|\busa\b|united states|miami|new york|texas|florida', 'Estados Unidos'),
    (r'honduras', 'Honduras'), (r'salvador', 'El Salvador'), (r'nicaragua', 'Nicaragua'),
    (r'puerto rico', 'Puerto Rico'), (r'\bcuba\b', 'Cuba'), (r'canada', 'Canada'),
    (r'reino unido|united kingdom|london', 'Reino Unido'), (r'portugal', 'Portugal'),
    (r'italia', 'Italia'), (r'francia', 'Francia'), (r'alemania', 'Alemania'),
]


def pais_norm(p):
    n = norm(p)
    if not n:
        return "N/D"
    for pat, lab in PAIS_MAP:
        if re.search(pat, n):
            return lab
    return p.strip()[:22] if p.strip() else "N/D"


def field(txt, name):
    m = re.search(r'^\*\*' + name + r':\*\*[ \t]*(.*)$', txt, re.M | re.I)
    return m.group(1).strip() if m else ""


def sec_body(txt, pat):
    out, cur = [], None
    for line in txt.split('\n'):
        if line.startswith('## '):
            cur = line[3:].strip()
        elif cur and re.search(pat, norm(cur)):
            out.append(line)
    return '\n'.join(out).strip()


rows = []
for mes in MESES:
    d = os.path.join(BASE, 'conversaciones', mes)
    if not os.path.isdir(d):
        continue
    for fn in os.listdir(d):
        if not fn.endswith('.md'):
            continue
        try:
            txt = open(os.path.join(d, fn), encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        heads = [l[3:].strip() for l in txt.split('\n') if l.startswith('## ')]
        hn = [norm(h) for h in heads]
        nombre = txt.split('\n')[0].lstrip('# ').strip() if txt.startswith('#') else fn[:-3]
        estado = field(txt, 'Estado')
        mconf = re.search(r'\*\*Confidence:\*\*[ \t]*(\w+)', txt)
        conf = (mconf.group(1) if mconf else "").upper()

        def tiene(p):
            return any(re.search(p, h) for h in hn)

        resp1 = tiene(r'^respuesta msg1|^respuesta y seguimiento|^respuesta$|^conversacion')
        resp2 = tiene(r'^respuesta msg2')
        msg2 = tiene(r'^msg2')
        seg1 = tiene(r'^seg1|^seguimiento 1')
        seg2 = tiene(r'^seg2')
        msg3 = tiene(r'^msg3')
        est = norm(estado)
        notas = sec_body(txt, r'^notas')
        dossier = tiene(r'^dossier') or bool(re.search(r'dossier (enviado|confirmado|por mail)', est))
        cierre = tiene(r'^cierre')
        respuesta_txt = sec_body(txt, r'^respuesta')
        nointeres = bool(re.search(r'sin interes|no interesad|cerrad|declin|rechaz', est + ' ' + norm(notas)[:400]))
        reunion = bool(re.search(r'reunion agendada|call agendada|reunion confirmada|meet agendad', norm(txt)))
        rows.append(dict(
            mes=mes, file=fn, nombre=nombre, cargo=field(txt, 'Cargo'), empresa=field(txt, 'Empresa'),
            pais=pais_norm(field(txt, 'Pais') or field(txt, 'Pa.s')), sector_raw=field(txt, 'Sector'),
            sector=sector_norm(field(txt, 'Sector')), estado=estado, confidence=conf,
            genero=genero(nombre), seniority=seniority(field(txt, 'Cargo')),
            resp1=resp1, resp2=resp2, msg2=msg2, msg3=msg3, seg1=seg1, seg2=seg2,
            dossier=dossier, cierre=cierre, nointeres=nointeres, reunion=reunion,
            len_resp=len(respuesta_txt), resp_txt=respuesta_txt[:3000], notas=notas[:1500],
            fecha=field(txt, 'Fecha')))

json.dump(rows, open(os.path.join(HERE, 'rows.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print("total", len(rows))
for mes in MESES:
    r = [x for x in rows if x['mes'] == mes]
    if not r:
        continue
    n = len(r)
    rp = sum(x['resp1'] for x in r)
    do = sum(x['dossier'] for x in r)
    print("%-11s n=%4d resp=%3d (%4.1f%%) msg2=%3d dossier=%3d (%4.1f%%) seg1=%3d reunion=%d noint=%d" % (
        mes, n, rp, rp / n * 100, sum(x['msg2'] for x in r), do, do / n * 100,
        sum(x['seg1'] for x in r), sum(x['reunion'] for x in r), sum(x['nointeres'] for x in r)))
