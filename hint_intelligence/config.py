import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIE_DIR  = os.path.dirname(os.path.abspath(__file__))

# ── Fuentes de datos ──────────────────────────────────────────────────────────
HISTORIAL_DATASET  = os.path.join(BASE_DIR, 'dataset_builder', 'outputs', 'historial_dataset.json')
DATASET_JSON       = os.path.join(BASE_DIR, 'dataset_builder', 'outputs', 'dataset.json')
STATS_JSON         = os.path.join(BASE_DIR, 'dataset_builder', 'outputs', 'stats.json')
ENRICHED_CSV       = os.path.join(BASE_DIR, 'ai_enrichment', 'outputs', 'enriched_dataset.csv')

# ── Outputs ───────────────────────────────────────────────────────────────────
KB_DIR             = os.path.join(HIE_DIR, 'knowledge_base')
OUTPUTS_DIR        = os.path.join(HIE_DIR, 'outputs')

KB_PATTERNS        = os.path.join(KB_DIR, 'patterns.json')
KB_SECTORS         = os.path.join(KB_DIR, 'sector_intelligence.json')
KB_SIGNALS         = os.path.join(KB_DIR, 'signals.json')
KB_OBJECTIONS      = os.path.join(KB_DIR, 'objection_playbook.json')
KB_EXPERIMENTS     = os.path.join(KB_DIR, 'experiment_history.json')

OUT_REPORT         = os.path.join(OUTPUTS_DIR, 'intelligence_report.md')
OUT_CONTEXT        = os.path.join(OUTPUTS_DIR, 'context_injection.json')
OUT_ALERTS         = os.path.join(OUTPUTS_DIR, 'alerts.json')
OUT_EXPERIMENTS    = os.path.join(OUTPUTS_DIR, 'experiments_queue.json')
OUT_LOG            = os.path.join(OUTPUTS_DIR, 'engine_log.json')

# ── Umbrales de confianza ─────────────────────────────────────────────────────
CONFIDENCE_THRESHOLDS = {
    'INSUFFICIENT': (0,  9),    # n < 10  → no concluir nada
    'LOW':          (10, 29),   # n 10-29 → hipótesis
    'MEDIUM':       (30, 99),   # n 30-99 → patrón
    'HIGH':         (100, 9999) # n >= 100 → regla
}

# Umbral mínimo para que un insight aparezca en el reporte
MIN_N_FOR_REPORT = 3

# Umbral de cambio para alertas (puntos porcentuales)
CHANGE_ALERT_THRESHOLD_PCT = 10.0
MIN_N_FOR_CHANGE_ALERT = 5

# Sectores que el sistema conoce (para context_injection)
KNOWN_SECTORS = [
    'Energía', 'Farmacéutico', 'Real Estate', 'Seguros/Finanzas', 'Minería',
    'Automotriz', 'Tecnología', 'Agencia/Marketing', 'Retail/Consumo',
    'Consultoría/Legal', 'Salud/Clínica', 'Educación', 'Turismo/Hotelería',
    'Agro/Alimentos', 'Logística/Transporte', 'Construcción/Materiales',
    'ONG/Fundación', 'Medios/Comunicación',
]

# Clientes Hint por sector (para context_injection)
HINT_CLIENTS_BY_SECTOR = {
    'Energía':            ['TGS', 'Transener'],
    'Minería':            ['TGS', 'Transener'],
    'Construcción/Materiales': ['TGS', 'Transener'],
    'Seguros/Finanzas':   ['Libra Seguros', 'Destiny Group'],
    'Consultoría/Legal':  ['Destiny Group', 'Libra Seguros'],
    'Tecnología':         ['Destiny Group', 'Libra Seguros'],
    'Retail/Consumo':     ['Destiny Group', 'Tasarolli'],
    'Agencia/Marketing':  ['Destiny Group', 'Tasarolli'],
    'Farmacéutico':       ['Libra Seguros', 'Destiny Group'],
    'Salud/Clínica':      ['Libra Seguros', 'Destiny Group'],
    'ONG/Fundación':      ['Destiny Group', 'Libra Seguros'],
}
DEFAULT_CLIENTS = ['Destiny Group', 'Libra Seguros']
