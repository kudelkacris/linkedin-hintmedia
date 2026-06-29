import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSACIONES_DIR = os.path.join(BASE_DIR, 'conversaciones')
DATASET_JSON = os.path.join(BASE_DIR, 'dataset_builder', 'outputs', 'dataset.json')
NEEDS_AI_CSV = os.path.join(BASE_DIR, 'dataset_builder', 'outputs', 'needs_ai_review.csv')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
ENV_LOCAL = os.path.join(BASE_DIR, '.env.local')

API_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-haiku-4-5-20251001'

# Campos que este pipeline puede llenar SI Y SOLO SI están vacíos en el dataset original.
TARGET_FIELDS = [
    'SECTOR', 'AREA', 'NIVEL_SENIORITY', 'TIPO_PERFIL',
    'ENGAGEMENT_LEVEL', 'OBJECION_PRINCIPAL', 'MOTIVO_EXITO', 'MOTIVO_FRACASO',
]

# Enums válidos por campo. Si el modelo devuelve algo fuera de esta lista, se descarta
# (no se inventa una categoría nueva ni se fuerza un mapeo).
VALID_VALUES = {
    'NIVEL_SENIORITY': {'CEO', 'VP', 'DIRECTOR', 'MANAGER', 'SPECIALIST', 'OTHER'},
    'TIPO_PERFIL': {'DECISION_MAKER', 'INFLUENCER', 'PARTNER', 'SPECIALIST'},
    'ENGAGEMENT_LEVEL': {'LOW', 'MEDIUM', 'HIGH'},
    'OBJECION_PRINCIPAL': {
        'NONE', 'HAS_AGENCY', 'BAD_TIMING', 'NO_BUDGET', 'PARTNERSHIP',
        'CURIOSITY_ONLY', 'SOFT_NO', 'HARD_NO', 'HIGH_INTENT', 'WARM_INTENT',
    },
}
# SECTOR, AREA, MOTIVO_EXITO, MOTIVO_FRACASO son texto libre, sin enum.

CONFIDENCE_LEVELS = {'HIGH', 'MEDIUM', 'LOW'}

MAX_REASON_WORDS = 50
MAX_MOTIVO_WORDS = 40

DEFAULT_TEST_LIMIT = 20
