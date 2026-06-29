import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSACIONES_DIR = os.path.join(BASE_DIR, 'conversaciones')
HISTORIAL_PATH = os.path.join(BASE_DIR, 'historial.json')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

FIELDS = [
    'ID_CONVERSACION', 'PROSPECTO', 'EMPRESA', 'PAIS', 'SECTOR', 'CARGO',
    'NIVEL_SENIORITY', 'TIPO_PERFIL', 'ESTADO_ACTUAL', 'VARIANTE_MSG1',
    'MSG1', 'RESPONDIO_MSG1', 'MSG2', 'PIDIO_DOSSIER', 'DOSSIER_ENVIADO',
    'RESPONDIO_DOSSIER', 'SEG1_ENVIADO', 'SEG2_ENVIADO', 'OBJECION_PRINCIPAL',
    'ENGAGEMENT_LEVEL', 'CALL_AGENDADA', 'CLIENTE_CERRADO', 'RESULTADO_FINAL',
    'MOTIVO_EXITO', 'MOTIVO_FRACASO', 'OBSERVACIONES', 'FUENTE_ARCHIVO',
]

NEEDS_AI_FIELDS = ['OBJECION_PRINCIPAL', 'ENGAGEMENT_LEVEL', 'MOTIVO_EXITO', 'MOTIVO_FRACASO', 'TIPO_PERFIL']

# ─── Heurísticas de objeción (orden = prioridad de match) ──────────────
OBJECTION_RULES = [
    ('HAS_AGENCY', [r'tenemos agencia', r'ya tienen agencia', r'ya tenemos equipo', r'ya contamos con (un )?equipo',
                     r'tenemos equipo (interno|propio)', r'trabajamos con (una )?agencia']),
    ('NO_BUDGET', [r'no (tenemos|hay) presupuesto', r'sin presupuesto', r'no contamos con presupuesto', r'no es el momento.*presupuesto']),
    ('BAD_TIMING', [r'no estamos buscando', r'no es el momento', r'por ahora no', r'más adelante', r'mas adelante',
                     r'no por el momento', r'todavía no', r'aun no es momento']),
    ('PARTNERSHIP', [r'colaboraci[oó]n', r'trabajar juntos', r'freelance', r'alianza', r'socios']),
    ('CURIOSITY_ONLY', [r'mandame el dossier', r'mándame el dossier', r'pasame el dossier', r'envíamelo', r'envíame(lo)?',
                         r'dale (mand|env)', r'si,? mandalo', r'si,? claro,? mandalo']),
]

# ─── Señales de CTA / reunión agendada ──────────────────────────────────
CALL_KEYWORDS = [r'\bteams\b', r'\bmeet\b', r'\bcall\b', r'\breuni[oó]n\b', r'\bagend', r'\b15 ?min', r'\bzoom\b',
                  r'\bcoordinamos\b.*\b(min|hora|llamada)', r'\bllamada\b']

# ─── Cierre de cliente ───────────────────────────────────────────────────
CLIENT_KEYWORDS = [r'cliente cerrado', r'firm[oó] contrato', r'contratado', r'ya es cliente', r'cerramos (el )?trato']

# ─── Seniority por cargo ─────────────────────────────────────────────────
SENIORITY_RULES = [
    ('CEO', [r'\bceo\b', r'fundador', r'co-?fundador', r'presidente', r'director general', r'gerente general']),
    ('VP', [r'\bvp\b', r'vicepresidente', r'vice president']),
    ('DIRECTOR', [r'director', r'directora', r'\bcdo\b', r'\bcco\b', r'\bcmo\b', r'chief']),
    ('MANAGER', [r'manager', r'gerente', r'jefe de', r'jefa de', r'l[ií]der de']),
    ('SPECIALIST', [r'especialista', r'analista', r'coordinador', r'coordinadora', r'asistente']),
]

# ─── Tipo de perfil (heurística simple, puede marcar NEEDS_AI) ──────────
PROFILE_TYPE_RULES = [
    ('DECISION_MAKER', [r'\bceo\b', r'director', r'gerente general', r'fundador', r'\bvp\b', r'\bcmo\b', r'\bcco\b', r'\bcdo\b']),
    ('SPECIALIST', [r'especialista', r'analista', r'coordinador']),
    ('PARTNER', [r'colaboraci[oó]n', r'alianza', r'freelance']),
]

# ─── Sector por empresa + cargo (orden = prioridad) ─────────────────────
SECTOR_RULES = [
    ('Energía', [
        r'enap\b', r'edenor', r'aes andes', r'lipigas', r'abastible', r'tgs\b', r'transener',
        r'rigsa', r'richa de la guardia', r'gulf oil', r'growatt', r'energ[ií]a solar',
        r'generaci[oó]n el[eé]ctrica', r'oil.*gas', r'gas.*oil', r'combustible',
        r'distribuci[oó]n de gas', r'energ[ií]a el[eé]ctrica',
        r'ecopetrol', r'terpel', r'petrobras', r'promigas', r'electrisa', r'nucleoel[eé]ctrica',
        r'ypf\b', r'geopark', r'servipet', r'pampa energ[ií]a', r'arsat\b',
        r'imcc\b', r'marine construction', r'barrick gold', r'veladero',
    ]),
    ('Farmacéutico', [
        r'novartis', r'knight therapeutics', r'medipan', r'biofarma', r'farmac[eé]utic',
        r'abbott', r'laboratorio', r'salud\b.*\blatam',
        r'global pharma', r'adium\b', r'zoetis', r'siegfried', r'leterago', r'dermclar',
        r'federada salud', r'grupo omint',
    ]),
    ('Real Estate', [
        r'ecipsa', r'novogar', r'cfl inmobiliaria', r'inmobiliar', r'real estate',
        r'desarrollo inmobiliario', r'distrito panamera',
        r'roca alliances', r'regency properties', r'irsa\b', r'kukun\b',
    ]),
    ('Seguros/Finanzas', [
        r'libra seguros', r'destiny group', r'ans s\.a', r'intermediaci[oó]n de seguros',
        r'creditforce', r'fintech', r'cr[eé]dito.*software', r'lulubit',
        r'coopeuch', r'panacredit', r'ficohsa', r'santander', r'seedtrust', r'banca\b',
        r'pwc\b', r'tairo group',
    ]),
    ('Minería', [
        r'hca miner[ií]a', r'ingenalse', r'miner[ií]a', r'bhp\b', r'bureau veritas',
        r'newmont', r'antofagasta minerals', r'barrick', r'el pach[oó]n', r'vicpimar',
    ]),
    ('Automotriz', [
        r'grupo cori motors', r'forta tech.*automotriz', r'automotriz', r'motors\b',
        r'car one\b', r'grupo dinosaurio',
    ]),
    ('Tecnología', [
        r'factor k software', r'skydata', r'congero technology', r'bravent', r'hypernova',
        r'lina corporation', r'datalog', r'dataformas', r'software.*desarrollo',
        r'desarrollo de software', r'it\b.*\blatam', r'ai solutions', r'erp\b', r'crm\b.*saas',
        r'ncq technologies', r'tech.*software\b', r'unravel data', r'mas analytics',
        r'demeter innovation', r'gblab\b', r'moovin', r'magneto\b', r'xcmg\b',
        r'sistemas\b.*tecnolog', r'konzerta', r'troop\b',
    ]),
    ('Agencia/Marketing', [
        r'loymark', r'komunika', r'garnier.*agency', r'garnier.*digital', r'mccann',
        r'agencia digital', r'agencia.*marketing', r'agencia.*pr', r'agencia.*publicidad',
        r'el arroyo.*marketing', r'hummingbirds',
        r'markethinkstudio', r'yc marketing', r'publicidad.*marketing', r'marketing.*digital\b',
        r'soluciones de marketing', r'comunicaci[oó]n corporativa', r'crecimiento b2b',
    ]),
    ('Retail/Consumo', [
        r'colombiana de comercio', r'corbeta', r'alkosto', r'grupo inteca', r'nestle',
        r'intaco', r'grupo forco', r'porta hnos', r'grupo motta', r'percos',
        r'bingo loco', r'libertario coffee', r'tasarolli',
        r'regency brands', r'american beauty supply', r'grupo eurobelleza', r'cofersa\b',
        r'tortillas ilusi[oó]n', r'punto rojo', r'coop spirits', r'brunchit',
        r'open blue', r'bio-crop', r'pc central',
    ]),
    ('Consultoría/Legal', [
        r'fischer y c[ií]a', r'estudio legal', r'estudio.*tributario', r'bdo\b',
        r'accenture', r'consultora', r'consulting',
        r'colegio de abogados', r'dharma\b', r'veritas vas', r'audubon',
        r'vicuña\b', r'ide business school',
    ]),
    ('Salud/Clínica', [
        r'fundaci[oó]n favaloro', r'crl.*cl[ií]nica', r'cl[ií]nica', r'footprints mental health',
        r'kipclin', r'recuperaci[oó]n de lesiones',
        r'ihrmc\b', r'grupo omint',
    ]),
    ('Educación', [
        r'edutech', r'texas tech university', r'intensa.*language', r'language institute',
        r'universidad', r'tecnol[oó]gico de costa rica', r'esic\b', r'aden university',
        r'aden business school', r'ealde business school', r'louisiana state university',
        r'university of louisville', r'cnn radio',
    ]),
    ('Turismo/Hotelería', [
        r'hacienda altagracia', r'auberge resorts', r'hotel territorio', r'smy hotels',
        r'geoser', r'akira travel', r'geo tours', r'turismo', r'hotelería',
        r'evenia hotels', r'sls cancun', r'hotel las am[eé]ricas', r'magn[ií]fico.*hospitalidad',
        r'special places', r'costa rica vacations', r'altagracia.*hacienda',
        r'umusic hospitality', r'cala hotels', r'hamak hotels', r'nh\b.*hyatt',
        r'corporate stays', r'grupo pampa crc', r'eventos corporativos',
    ]),
    ('Agro/Alimentos', [
        r'corbana', r'bananera', r'grupo america.*zona franca',
        r'williamson industrial', r'grupo espumas', r'maxindustrias', r'melisam fire',
    ]),
    ('Logística/Transporte', [
        r'log[ií]stica panam[áa]', r'transporte\b', r'loginter\b', r'stuart\b',
        r'grupo panama car rental', r'ptl group',
    ]),
    ('Construcción/Materiales', [
        r'materiales de construcci[oó]n', r'acero\b', r'ternium\b', r'sidersa\b',
        r'cofersa\b',
    ]),
    ('ONG/Fundación', [
        r'fundaci[oó]n', r'movimiento laudato', r'la libertad.*fundaci[oó]n', r'ong\b',
        r'sportclub oficial',
    ]),
    ('Medios/Comunicación', [
        r'cnn radio', r'grupo am[eé]rica\b', r'comunicadora social',
    ]),
]

# ─── Engagement: si no está escrito explícito, heurística por señales ──
ENGAGEMENT_EXPLICIT_RE = r'engagement(?:_level)?[:\s]*\(?(HIGH|MEDIUM|LOW)\)?'

# ─── Mapeo de ESTADO_ACTUAL / RESULTADO_FINAL ───────────────────────────
RESULTADO_RULES = [
    ('CLIENTE', CLIENT_KEYWORDS),
    ('REUNION', [r'call agendada', r'reuni[oó]n agendada', r'llamada agendada', r'agendamos'] + CALL_KEYWORDS),
    ('SEGUIMIENTO', [r'\bseg1\b', r'\bseg2\b', r'seguimiento']),
    ('DOSSIER', [r'dossier enviado', r'dossier confirmado', r'dossier por mandar', r'dossier aceptado']),
]
