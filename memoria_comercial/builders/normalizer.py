"""
normalizer.py — HITO 4: convierte dict crudo del parser a ConversationRecord tipado.

Reglas:
  - Sin IA, sin inferencias especulativas: solo regex y reglas deterministas
  - Si una regla no puede decidir -> DESCONOCIDO, nunca inventa
  - Idempotente: mismo input = mismo output
  - Cada detect_* opera sobre texto en minusculas sin acentos (normalizado)
"""
import os
import re
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCHEMA_VERSION, PARSER_VERSION
from schemas.conversation import (
    ConversationRecord, SourceInfo, Metadata, Normalized,
    ConversationMessages, Signals, TextContent, QualityInfo,
)
from schemas.fields import (
    Sector, Seniority, TipoDecisor, ResultadoFinal,
    ObjecionPrincipal, EngagementLevel, VarianteMsg1,
)


# ── Tabla de acentos (reutilizada de parser) ─────────────────────────────────

_ACCENT = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _n(text: str) -> str:
    """Normaliza: minusculas + sin acentos. Base de todas las comparaciones."""
    return (text or "").lower().translate(_ACCENT).strip()


# ── Mapas de keywords para deteccion ─────────────────────────────────────────

# Sector: lista ordenada de (keywords, Sector). Primero mas especifico.
_SECTOR_RULES: List[Tuple[List[str], Sector]] = [
    # Amazon / Marketplace (mas especifico que retail)
    (["amazon", "walmart connect", "retail media", "marketplace"], Sector.AMAZON_ECOMMERCE),
    # Energia / Infra
    (["energia", "oil", "gas", "petro", "utilities", "electricidad", "agua potable",
      "mineras", "tgs", "transener", "gasdelsur", "gasoducto"], Sector.ENERGIA_INFRA),
    # Mineria
    (["mineria", "minero", "cobre", "litio", "ingenalse", "extraccion"], Sector.MINERIA),
    # Seguros / Finanzas
    (["seguro", "finanzas", "financiero", "banco", "fintech", "credito", "inversion",
      "wealth", "libra seguros", "destiny group"], Sector.SEGUROS_FINANZAS),
    # Farmaceutico / Salud
    (["farmac", "laboratorio", "salud", "clinica", "hospital", "medic", "oncolog",
      "biotech", "pharma"], Sector.FARMACEUTICO_SALUD),
    # Turismo / Eventos
    (["turismo", "hotel", "hostel", "eventos", "viaje", "travel", "catering"], Sector.TURISMO_EVENTOS),
    # Construccion / Real Estate
    (["inmobil", "construccion", "real estate", "desarrolladora", "ingenieria civil",
      "arquitectura", "property"], Sector.CONSTRUCCION),
    # Logistica
    (["logistica", "transporte", "cadena de suministro", "supply chain", "courier",
      "distribucion", "carga", "freight"], Sector.LOGISTICA),
    # Telecomunicaciones
    (["teleco", "telecom", "internet", "isp", "fibra", "movil", "cellular",
      "skydata", "telefonia"], Sector.TELECOMUNICACIONES),
    # Manufactura
    (["manufactura", "fabrica", "industrial", "produccion", "planta", "foamtec",
      "aluminio", "acero"], Sector.MANUFACTURA),
    # Alimentacion
    (["aliment", "bebida", "fmcg", "comida", "gastro", "food", "agro",
      "vino", "cerveza", "lacteo"], Sector.ALIMENTACION),
    # Agro
    (["agropecuario", "agro ", "campo", "ganado", "siembra", "cosecha"], Sector.AGRO),
    # Educacion
    (["educacion", "universidad", "edtech", "colegio", "formacion", "capacitacion",
      "escuela", "learning", "cimientos"], Sector.EDUCACION),
    # Gobierno / ONG
    (["gobierno", "ong", "ngo", "organismo", "municipio", "publico", "estado ",
      "ministerio", "fundacion", "asociacion", "advocacy"], Sector.GOBIERNO),
    # Belleza / Lujo
    (["belleza", "cosmetico", "lujo", "moda premium", "luxury", "perfume",
      "estetica", "spa"], Sector.BELLEZA_LUJO),
    # Retail / Moda (menos especifico que amazon/marketplace)
    (["retail", "moda", "tienda", "shop", "ecommerce", "e-commerce",
      "tasarolli", "indumentaria"], Sector.RETAIL_MODA),
    # Consultoria / Tech
    (["consultora", "consultoria", "agencia", "saas", "software", "tech",
      "digital", "datos", "ia", "inteligencia artificial", "automatizacion",
      "factor k", "anthropic"], Sector.CONSULTORIA_TECH),
    # Marketing / Comunicacion
    (["marketing", "comunicacion", "branding", "contenido", "relaciones publicas",
      "publicidad", "prensa", "pr "], Sector.MARKETING_BRANDING),
]

# Seniority: lista ordenada de (keywords, Seniority). Primero mas especifico.
_SENIORITY_RULES: List[Tuple[List[str], Seniority]] = [
    # CEO / Fundador
    (["ceo", "chief executive", "fundador", "cofundador", "presidente ejecutivo",
      "director general", "dueño", "propietario", "socio fundador"], Seniority.CEO),
    # VP
    (["vp ", "vice president", "svp", "evp", "vicepresidente", "vice presid"], Seniority.VP),
    # Director / Head of
    (["director", "head of", "chief ", "cto", "cmo", "coo", "cfo", "cpo"], Seniority.DIRECTOR),
    # Manager / Gerente / Jefe
    (["gerente", "manager", "jefe de", "jefe ", "encargado de", "responsable de",
      "líder de", "lider de", "lead "], Seniority.MANAGER),
    # Specialist / Analyst / Coordinator / Expert
    (["especialista", "analista", "coordinador", "specialist", "analyst", "associate",
      "ejecutivo de", "asesor", "consultor", "tecnico", "expert", "experto",
      "creativo", "strategist", "content"], Seniority.SPECIALIST),
]

# Objecion: keywords en texto del PROSPECTO (nunca de Hint)
_OBJECION_RULES: List[Tuple[List[str], ObjecionPrincipal]] = [
    (["equipo interno", "tenemos equipo", "hacemos en casa", "in-house",
      "propia area"], ObjecionPrincipal.INTERNAL_TEAM),
    (["ya tenemos agencia", "trabajamos con una agencia", "tenemos proveedor",
      "ya contamos con"], ObjecionPrincipal.HAS_AGENCY),
    (["sin presupuesto", "no tenemos presupuesto", "budget", "recorte",
      "restriccion presupuestaria"], ObjecionPrincipal.NO_BUDGET),
    (["no es el momento", "mal momento", "trimestre", "fin de año",
      "cambio de directiva", "restructuracion"], ObjecionPrincipal.BAD_TIMING),
    (["colaborar", "asociarnos", "partner", "co-crear", "intercambio"],
     ObjecionPrincipal.PARTNERSHIP),
]


# ── API publica ───────────────────────────────────────────────────────────────

def normalize(raw: Dict, conv_id: str, contact_id: str,
              source_info: Dict, created_at: str = None) -> ConversationRecord:
    """
    Orquesta la normalizacion completa.
    raw         <- dict crudo del parser
    conv_id     <- "conv_000001" asignado por index_builder
    contact_id  <- "ctc_000001" del ContactRecord correspondiente
    source_info <- {"file_hash", "file_modified", "file_size", "_source_file"}
    Retorna ConversationRecord serializable.
    """
    now = _utc_now()
    src_file = source_info.get("_source_file", "")

    # ── SourceInfo ────────────────────────────────────────────────────────────
    month_folder = _extract_month_folder(src_file)
    source = SourceInfo(
        file_path=src_file,
        file_hash=source_info.get("_fingerprint", source_info.get("file_hash", "")),
        file_modified=source_info.get("file_modified", ""),
        file_size=source_info.get("file_size", 0),
        month_folder=month_folder,
    )

    # ── Metadata (raw) ────────────────────────────────────────────────────────
    metadata = Metadata(
        nombre=raw.get("nombre", ""),
        empresa=raw.get("empresa", ""),
        cargo=raw.get("cargo", ""),
        pais=raw.get("pais", ""),
        fecha=raw.get("fecha", ""),
        estado_texto=raw.get("estado", ""),
    )

    # ── Normalizacion: detect_* ───────────────────────────────────────────────
    sector_raw = raw.get("sector", "")
    cargo = raw.get("cargo", "")
    empresa = raw.get("empresa", "")
    estado = raw.get("estado", "")
    notas = raw.get("notas", "")

    sector_val = detect_sector(empresa, cargo, sector_raw)
    seniority_val = detect_seniority(cargo)
    tipo_decisor_val = detect_tipo_decisor(cargo, seniority_val)
    stage_val = detect_stage(estado, raw)
    engagement_val = detect_engagement(raw)
    variante_val = detect_variante_msg1(raw.get("msg1_texto", ""))

    # Objecion: solo en respuestas del prospecto
    respuestas = "\n".join(filter(None, [
        raw.get("resp_msg1_texto", ""),
        raw.get("resp_msg2_texto", ""),
        raw.get("cierre_texto", ""),
    ]))
    objecion_val = detect_objecion(respuestas, notas)

    respondio = bool(raw.get("resp_msg1_texto", ""))
    dossier_enviado = bool(raw.get("msg3_texto", "")) or stage_val >= 3
    call_agendada = stage_val == 6 or _has_keyword(estado, ["reunion agendada", "call agendada", "call programada"])

    resultado_val = detect_resultado(
        stage=stage_val,
        respondio=respondio,
        dossier=dossier_enviado,
        call=call_agendada,
        cerrado=_has_keyword(estado + " " + notas, ["cerrada", "cerrado", "no interes", "no hay fit"]),
    )

    normalized = Normalized(
        sector=Sector(sector_val),
        seniority=Seniority(seniority_val),
        tipo_decisor=TipoDecisor(tipo_decisor_val),
        stage=stage_val,
        resultado_final=ResultadoFinal(resultado_val),
        objecion_principal=ObjecionPrincipal(objecion_val),
        engagement_level=EngagementLevel(engagement_val),
        variante_msg1=VarianteMsg1(variante_val),
    )

    # ── ConversationMessages ──────────────────────────────────────────────────
    conversation = ConversationMessages(
        msg1_texto=raw.get("msg1_texto", ""),
        respondio_msg1=respondio,
        respuesta_msg1_texto=raw.get("resp_msg1_texto", ""),
        msg2_texto=raw.get("msg2_texto", ""),
        dossier_enviado=dossier_enviado,
        respondio_dossier=bool(raw.get("resp_msg2_texto", "")),
        respuesta_dossier_texto=raw.get("resp_msg2_texto", ""),
        seg1_enviado=bool(raw.get("seg1_texto", "")) or stage_val == 4,
        seg1_texto=raw.get("seg1_texto", ""),
        seg2_enviado=bool(raw.get("seg2_texto", "")) or stage_val == 5,
        seg2_texto=raw.get("seg2_texto", ""),
        call_agendada=call_agendada,
        cliente_cerrado=bool(raw.get("cierre_texto", "")),
    )

    # ── Signals ───────────────────────────────────────────────────────────────
    palabras_clave = _extract_keywords(respuestas)
    signals = Signals(
        señal_humana=raw.get("senal_humana", ""),
        hipotesis=raw.get("hipotesis", ""),
        palabras_clave=palabras_clave,
        notas=notas,
    )

    # ── TextContent ───────────────────────────────────────────────────────────
    text = TextContent(
        conversation_text=raw.get("conversation_text", ""),
        raw_md=raw.get("raw_md", ""),
    )

    # ── QualityInfo ───────────────────────────────────────────────────────────
    campos_vacios, confidence = compute_confidence({
        "nombre": metadata.nombre,
        "empresa": metadata.empresa,
        "cargo": metadata.cargo,
        "sector": sector_val,
        "seniority": seniority_val,
        "stage": str(stage_val),
        "msg1_texto": conversation.msg1_texto,
        "resp_msg1": conversation.respuesta_msg1_texto,
    })
    quality = QualityInfo(
        campos_vacios=campos_vacios,
        parse_warnings=raw.get("parse_warnings", []),
        parse_errors=raw.get("parse_errors", []),
        confidence_score=confidence,
    )

    return ConversationRecord(
        conversation_id=conv_id,
        contact_id=contact_id,
        source_file=src_file,
        fingerprint=source.file_hash,
        created_at=created_at or now,
        updated_at=now,
        schema_version=SCHEMA_VERSION,
        parser_version=PARSER_VERSION,
        build_date=now,
        source=source,
        metadata=metadata,
        normalized=normalized,
        conversation=conversation,
        signals=signals,
        text=text,
        quality=quality,
    )


def detect_sector(empresa: str, cargo: str, sector_raw: str) -> str:
    """
    Infiere sector desde sector_raw (campo **Sector:** del .md) con fallback a empresa+cargo.
    Retorna Sector enum value.
    """
    # Paso 1: usar sector_raw solo (campo **Sector:** es la senial mas explicita)
    sector_n = _n(sector_raw)
    if sector_n:
        for keywords, sector in _SECTOR_RULES:
            if any(kw in sector_n for kw in keywords):
                return sector.value

    # Paso 2: empresa + sector_raw combinados
    combined = sector_n + " " + _n(empresa)
    for keywords, sector in _SECTOR_RULES:
        if any(kw in combined for kw in keywords):
            return sector.value

    # Paso 3: cargo como ultimo recurso
    cargo_n = _n(cargo)
    for keywords, sector in _SECTOR_RULES:
        if any(kw in cargo_n for kw in keywords):
            return sector.value

    return Sector.DESCONOCIDO.value


def detect_seniority(cargo: str) -> str:
    """
    Infiere seniority desde cargo. Prioridad: mas alto primero.
    Retorna Seniority enum value.
    """
    cargo_n = _n(cargo)
    for keywords, seniority in _SENIORITY_RULES:
        if any(kw in cargo_n for kw in keywords):
            return seniority.value
    return Seniority.DESCONOCIDO.value


def detect_tipo_decisor(cargo: str, seniority: str) -> str:
    """
    Infiere tipo de decisor desde seniority.
    CEO/VP/DIRECTOR -> DECISION_MAKER
    MANAGER -> INFLUENCER (asume que necesita aprobacion superior)
    SPECIALIST -> SPECIALIST
    """
    mapping = {
        Seniority.CEO.value:        TipoDecisor.DECISION_MAKER.value,
        Seniority.VP.value:         TipoDecisor.DECISION_MAKER.value,
        Seniority.DIRECTOR.value:   TipoDecisor.DECISION_MAKER.value,
        Seniority.MANAGER.value:    TipoDecisor.INFLUENCER.value,
        Seniority.SPECIALIST.value: TipoDecisor.SPECIALIST.value,
    }
    return mapping.get(seniority, TipoDecisor.DESCONOCIDO.value)


def detect_stage(estado_texto: str, raw: Dict) -> int:
    """
    Infiere stage (1-6) desde estado_texto. Prioridad: estado explicito > secciones presentes.
    Nunca baja: si ya hay MSG3 en el .md, el stage es al menos 3.
    """
    estado_n = _n(estado_texto)

    # Deteccion explicita por texto (mayor prioridad)
    if _has_keyword(estado_n, ["reunion agendada", "call agendada", "call programada",
                                "meeting agendad", "stage 6", "stage: 6"]):
        return 6
    if _has_keyword(estado_n, ["seg2 enviado", "seguimiento 2 enviado"]):
        return 5
    if _has_keyword(estado_n, ["seg1 enviado", "seguimiento 1 enviado", "seguimiento enviado"]):
        return 4
    if _has_keyword(estado_n, ["dossier enviado", "dossier por mail", "dossier confirmado",
                                "msg3 enviado", "dossier por aca"]):
        return 3
    if _has_keyword(estado_n, ["msg2 enviado", "esperando respuesta al msg2",
                                "esperando respuesta msg2"]):
        return 2
    if _has_keyword(estado_n, ["msg1 enviado"]):
        return 1

    # Fallback: inferir desde secciones presentes en el parsed
    if raw.get("seg2_texto"):
        return 5
    if raw.get("seg1_texto"):
        return 4
    if raw.get("msg3_texto") or raw.get("resp_msg2_texto"):
        return 3
    if raw.get("msg2_texto"):
        return 2
    if raw.get("msg1_texto"):
        return 1

    return 1   # default: MSG1 enviado si hay .md


def detect_objecion(respuestas_texto: str, notas: str) -> str:
    """
    Detecta objecion principal SOLO en texto del prospecto y notas.
    Retorna ObjecionPrincipal enum value.
    """
    combined = _n(respuestas_texto + " " + notas)
    for keywords, objecion in _OBJECION_RULES:
        if any(kw in combined for kw in keywords):
            return objecion.value
    # Sin objecion detectada (puede ser EN_PROCESO o simplemente no respondio)
    return ObjecionPrincipal.NONE.value


def detect_engagement(raw: Dict) -> str:
    """
    Detecta engagement level.
    Prioridad: texto explicito en notas/estado > heuristica de longitud.
    """
    estado_n = _n(raw.get("estado", ""))
    notas_n = _n(raw.get("notas", ""))
    combined = estado_n + " " + notas_n

    # Texto explicito
    if "high" in combined or "alto" in combined and "engagement" in combined:
        return EngagementLevel.HIGH.value
    if "medium" in combined or "medio" in combined and "engagement" in combined:
        return EngagementLevel.MEDIUM.value
    if "low" in combined or "bajo" in combined and "engagement" in combined:
        return EngagementLevel.LOW.value

    # Heuristica: longitud de la respuesta MSG1
    resp = raw.get("resp_msg1_texto", "")
    if not resp:
        return EngagementLevel.DESCONOCIDO.value

    words = len(resp.split())
    if words >= 40:
        return EngagementLevel.HIGH.value
    if words >= 10:
        return EngagementLevel.MEDIUM.value
    return EngagementLevel.LOW.value


def detect_variante_msg1(msg1_texto: str) -> str:
    """
    Variante A: apertura por publicacion/reflexion personal (senial humana)
    Variante C: apertura por logro/resultado/trabajo concreto
    """
    msg_n = _n(msg1_texto)
    # Variante C: apertura por logro/trabajo/resultado CONCRETO
    # "resultado" solo es C cuando va con verbo de logro, no como concepto generico
    if any(kw in msg_n for kw in [
        "effie", "premio", "lograste", "implementaste", "lanzaste",
        "construiste", "campana que ", "iniciativa que ", "lograron",
        "fue seleccionado", "ganaron", "incrementaste", "redujiste",
    ]):
        return VarianteMsg1.C.value
    # Variante A: publicacion, reflexion, lo que compartes/compartiste/compartas
    if any(kw in msg_n for kw in [
        "publicacion", "publico", "publicaste", "compartiste", "escribiste",
        "leí tu", "lei tu", "me llamo la atencion", "contenido que",
        "reflexion", "critica", "compartas", "comparte", "compartes",
        "lo que lei", "lo que lei", "lo que vi", "me quedo ",
        "ultimos dias", "dias compartas", "me llamo la atencion",
    ]):
        return VarianteMsg1.A.value
    return VarianteMsg1.DESCONOCIDA.value


def detect_resultado(stage: int, respondio: bool, dossier: bool,
                     call: bool, cerrado: bool) -> str:
    """
    Determina resultado_final combinando stage y flags.
    """
    if call or stage == 6:
        return ResultadoFinal.REUNION.value
    if cerrado:
        return ResultadoFinal.CERRADO_SIN_INTERES.value
    if dossier or stage >= 3:
        return ResultadoFinal.EN_PROCESO.value
    if not respondio and stage == 1:
        return ResultadoFinal.SIN_RESPUESTA.value
    return ResultadoFinal.EN_PROCESO.value


def compute_confidence(fields: Dict) -> Tuple[List[str], float]:
    """
    Calcula confidence_score: fraccion de campos con valor no vacio / no DESCONOCIDO.
    Retorna (lista_campos_vacios, score_float).
    """
    vacios = []
    total = len(fields)
    llenos = 0

    for campo, valor in fields.items():
        if not valor or "DESCONOCIDO" in str(valor).upper():
            vacios.append(campo)
        else:
            llenos += 1

    score = round(llenos / total, 2) if total > 0 else 0.0
    return vacios, score


# ── Helpers privados ──────────────────────────────────────────────────────────

def _utc_now() -> str:
    """ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _has_keyword(text: str, keywords: List[str]) -> bool:
    """True si alguna keyword esta en el texto (normalizado)."""
    text_n = _n(text)
    return any(kw in text_n for kw in keywords)


def _extract_month_folder(file_path: str) -> str:
    """
    Extrae el nombre de la carpeta de mes desde la ruta.
    "conversaciones/julio/silvia.md" -> "julio"
    """
    parts = file_path.replace("\\", "/").split("/")
    # Buscar la carpeta justo antes del archivo (ultimo segmento)
    if len(parts) >= 2:
        return parts[-2]
    return ""


def _extract_keywords(respuestas_texto: str) -> List[str]:
    """
    Extrae tokens significativos de las respuestas del prospecto.
    Filtra stopwords comunes. Maximo 10 keywords.
    """
    if not respuestas_texto:
        return []

    _STOPWORDS = {
        "de", "la", "el", "en", "un", "una", "y", "a", "es", "que",
        "me", "lo", "se", "con", "por", "para", "del", "los", "las",
        "al", "te", "mi", "su", "si", "pero", "como", "muy", "mas",
        "no", "si", "o", "e", "ni", "gracias", "hola", "buenos", "buenas",
        "claro", "ok", "yes", "hi", "the", "and", "or", "of", "to",
    }

    words = re.findall(r"\b[a-záéíóúüñ]{4,}\b", _n(respuestas_texto))
    seen = set()
    keywords = []
    for w in words:
        if w not in _STOPWORDS and w not in seen:
            seen.add(w)
            keywords.append(w)
        if len(keywords) >= 10:
            break
    return keywords
