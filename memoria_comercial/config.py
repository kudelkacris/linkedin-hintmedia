"""
config.py — Memoria Comercial: rutas, versiones y constantes.
Sin lógica de negocio. Solo configuración.

Arquitectura de dos niveles:
  NIVEL 1 — CONTACTS    fuente: historial.json  (541 registros)
  NIVEL 2 — CONVERSATIONS  fuente: .md files    (276 archivos)
Un contacto puede existir sin conversación.
Una conversación siempre pertenece a un contacto.
"""
import os

# ── Versiones ──────────────────────────────────────────────────────────────────
SCHEMA_VERSION   = "1.0.0"
PARSER_VERSION   = "1.0.0"
DATASET_VERSION  = "1.0.0"

# ── Raíces ────────────────────────────────────────────────────────────────────
MC_ROOT              = os.path.dirname(os.path.abspath(__file__))
LINKEDIN_ROOT        = os.path.dirname(MC_ROOT)
CONVERSACIONES_ROOT  = os.path.join(LINKEDIN_ROOT, "conversaciones")
HISTORIAL_PATH       = os.path.join(LINKEDIN_ROOT, "historial.json")  # fuente NIVEL 1 (solo lectura)

# ── Dataset — raíz ────────────────────────────────────────────────────────────
DATASET_DIR          = os.path.join(MC_ROOT, "dataset")
MANIFEST_PATH        = os.path.join(DATASET_DIR, "manifest.json")

# ── Dataset — Nivel 1: CONTACTS ───────────────────────────────────────────────
CONTACTS_DIR          = os.path.join(DATASET_DIR, "contacts")
CONTACTS_INDEX_PATH   = os.path.join(DATASET_DIR, "contacts_index.json")
CONTACTS_REGISTRY_PATH = os.path.join(DATASET_DIR, "contacts_registry.json")

# ── Dataset — Nivel 2: CONVERSATIONS ─────────────────────────────────────────
CONVERSATIONS_DIR         = os.path.join(DATASET_DIR, "conversations")
CONVERSATIONS_INDEX_PATH  = os.path.join(DATASET_DIR, "conversations_index.json")
ID_REGISTRY_PATH          = os.path.join(DATASET_DIR, "id_registry.json")  # conv IDs
CSV_PATH                  = os.path.join(DATASET_DIR, "conversations.csv")

# ── Reports ───────────────────────────────────────────────────────────────────
REPORTS_DIR          = os.path.join(MC_ROOT, "reports")
COVERAGE_REPORT_PATH = os.path.join(REPORTS_DIR, "coverage_report.md")
QUALITY_REPORT_PATH  = os.path.join(REPORTS_DIR, "quality_report.md")

# ── Intelligence (Commercial Intelligence Engine) ─────────────────────────────
INTELLIGENCE_DIR            = os.path.join(MC_ROOT, "intelligence")
INTELLIGENCE_EMBEDDINGS_DIR = os.path.join(INTELLIGENCE_DIR, "embeddings")
INTELLIGENCE_CLUSTERS_DIR   = os.path.join(INTELLIGENCE_DIR, "clusters")
INTELLIGENCE_RECOMM_DIR     = os.path.join(INTELLIGENCE_DIR, "recommendations")
INTELLIGENCE_PATTERNS_DIR   = os.path.join(INTELLIGENCE_DIR, "patterns")
INTELLIGENCE_MEMORY_DIR     = os.path.join(INTELLIGENCE_DIR, "memory")

# ── Analysis ──────────────────────────────────────────────────────────────────
ANALYSIS_DIR         = os.path.join(MC_ROOT, "analysis")

# ── Tests ─────────────────────────────────────────────────────────────────────
TESTS_DIR            = os.path.join(MC_ROOT, "tests")

# ── Cache & Logs ──────────────────────────────────────────────────────────────
CACHE_PATH           = os.path.join(MC_ROOT, "cache", "raw_parsed.json")
BUILD_LOG_PATH       = os.path.join(MC_ROOT, "logs", "build.log")

# ── IDs — Conversations ───────────────────────────────────────────────────────
CONV_ID_PREFIX  = "conv_"
CONV_ID_PADDING = 6      # conv_000001

# ── IDs — Contacts ────────────────────────────────────────────────────────────
CONTACT_ID_PREFIX  = "ctc_"
CONTACT_ID_PADDING = 6   # ctc_000001

# ── Crawler ───────────────────────────────────────────────────────────────────
MD_EXTENSION = ".md"

# ── Fingerprinting ────────────────────────────────────────────────────────────
HASH_ALGORITHM = "sha256"
