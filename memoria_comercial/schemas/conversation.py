"""
conversation.py — ConversationRecord: schema completo de una conversación.
Fuente de verdad del modelo de datos. Sin lógica de negocio.

Cada instancia corresponde a un archivo conv_XXXXXX.json en dataset/conversations/.
Diseñado para evolucionar hacia un Commercial Intelligence Engine:
todos los campos reservados están documentados al final del archivo.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from .fields import (
    Sector, Seniority, TipoDecisor, ResultadoFinal,
    ObjecionPrincipal, EngagementLevel, VarianteMsg1
)


@dataclass
class SourceInfo:
    """Trazabilidad completa al archivo .md original."""
    file_path: str       # relativo a LINKEDIN_ROOT (ej: conversaciones/julio/andrea-robles.md)
    file_hash: str       # "sha256:abc123..." — fingerprint del archivo
    file_modified: str   # ISO 8601 UTC — mtime del .md
    file_size: int       # bytes
    month_folder: str    # nombre de la carpeta (junio, julio, agosto...)


@dataclass
class Metadata:
    """Campos crudos tal como aparecen en el .md. Sin normalizar."""
    nombre: str
    empresa: str
    cargo: str
    pais: str
    fecha: str          # DD/MM/YY raw
    estado_texto: str   # raw del campo **Estado:** en el .md


@dataclass
class Normalized:
    """Campos normalizados con enums. Construidos por el normalizer."""
    sector: Sector
    seniority: Seniority
    tipo_decisor: TipoDecisor
    stage: int                      # 1–6 (int puro para aritmética)
    resultado_final: ResultadoFinal
    objecion_principal: ObjecionPrincipal
    engagement_level: EngagementLevel
    variante_msg1: VarianteMsg1


@dataclass
class ConversationMessages:
    """Texto y flags de cada paso de la conversación."""
    msg1_texto: str
    respondio_msg1: bool
    respuesta_msg1_texto: str

    msg2_texto: str
    dossier_enviado: bool
    respondio_dossier: bool
    respuesta_dossier_texto: str

    seg1_enviado: bool
    seg1_texto: str
    seg2_enviado: bool
    seg2_texto: str

    call_agendada: bool
    cliente_cerrado: bool


@dataclass
class Signals:
    """Señales cualitativas extraídas del análisis del .md."""
    señal_humana: str           # texto de ## Análisis → Señal humana
    hipotesis: str              # texto de ## Análisis → Hipótesis
    palabras_clave: List[str]   # tokens extraídos de respuestas del prospecto
    notas: str                  # sección ## Notas


@dataclass
class TextContent:
    """
    Textos completos de la conversación en dos formatos.
    conversation_text: texto limpio para embeddings futuros.
    raw_md: backup exacto del archivo, inmune a modificaciones del .md original.
    """
    conversation_text: str   # sin >, **, ##, md markup
    raw_md: str              # contenido exacto del archivo .md


@dataclass
class QualityInfo:
    """Resultado del proceso de parsing y normalización."""
    campos_vacios: List[str]      # campos que quedaron vacíos o DESCONOCIDO
    parse_warnings: List[str]     # advertencias no fatales durante el parsing
    parse_errors: List[str]       # errores que impidieron extraer algún campo
    confidence_score: float       # 0.0–1.0: fracción de campos extraídos exitosamente


@dataclass
class ConversationRecord:
    """
    Documento completo de una conversación.
    Se serializa como conv_XXXXXX.json en dataset/conversations/.

    Diseñado para ser la fuente de verdad del Commercial Intelligence Engine.
    Los campos top-level (conversation_id, fingerprint, source_file, created_at, updated_at)
    permiten acceso rápido sin deserializar los bloques anidados.
    """

    # ── Identificación top-level ─────────────────────────────────────────────
    conversation_id: str    # conv_000001 — permanente, nunca cambia aunque el .md se mueva
    contact_id: str         # ctc_000001 — referencia al ContactRecord (Nivel 1)
                            # una conversación SIEMPRE pertenece a un contacto
    source_file: str        # shorthand: "conversaciones/julio/andrea-robles.md"
                            # mirrors source.file_path — para acceso rápido
    fingerprint: str        # "sha256:abc123..." — mirrors source.file_hash
                            # para detección de cambios sin leer el bloque source
    created_at: str         # ISO 8601 UTC — primera vez que se construyó este documento
    updated_at: str         # ISO 8601 UTC — última vez que se actualizó (--update builds)

    # ── Versiones ────────────────────────────────────────────────────────────
    schema_version: str
    parser_version: str
    build_date: str         # ISO 8601 UTC — fecha de esta build específica

    # ── Bloques de datos ──────────────────────────────────────────────────────
    source: SourceInfo
    metadata: Metadata
    normalized: Normalized
    conversation: ConversationMessages
    signals: Signals
    text: TextContent
    quality: QualityInfo

    # ── Campos reservados — Commercial Intelligence Engine ────────────────────
    # Los siguientes campos se agregarán en fases futuras.
    # Están documentados aquí para que toda decisión de diseño los contemple.
    #
    # intelligence/embeddings/:
    #   embedding: List[float]         vector semántico de text.conversation_text
    #   embedding_model: str           modelo usado para generar el vector
    #   embedding_date: str            ISO 8601, cuándo se generó
    #
    # intelligence/clusters/:
    #   cluster_id: Optional[str]      cluster de conversaciones similares
    #   cluster_label: Optional[str]   etiqueta humana del cluster
    #   cluster_distance: float        distancia al centroide del cluster
    #
    # intelligence/recommendations/:
    #   recommended_strategy: str      estrategia recomendada basada en patrones
    #   recommended_msg2: str          variación de MSG2 sugerida por el engine
    #   recommended_seg1: str          variación de SEG1 sugerida por el engine
    #   commercial_score: float        0.0–1.0: probabilidad de conversión estimada
    #
    # intelligence/memory/:
    #   similarity_ids: List[str]      conv_ids más similares semánticamente
    #   reference_cases: List[str]     conv_ids usados como referencia para esta
    #
    # intelligence/patterns/:
    #   pattern_matches: List[str]     patrones detectados en esta conversación
    #   anomaly_score: float           0.0–1.0: qué tan atípica es esta conversación
