"""
parser.py — HITO 3: extrae datos crudos de archivos .md de conversaciones.

Reglas:
  - Nunca romper en campo faltante: string vacio + warning
  - Idempotente: mismo archivo = mismo resultado
  - No normaliza: responsabilidad del normalizer (HITO 4)
  - Maneja dos formatos: standard (jul) y frontmatter (algunos jun legacy)
  - Sin IA, sin inferencias: solo extrae lo que esta escrito
"""
import os
import re
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PARSER_VERSION


# ── Mapas de clasificacion ────────────────────────────────────────────────────

_SECTION_MAP: Dict[str, str] = {
    "analisis":                   "analisis",
    # Mensajes Hint
    "msg1":                       "msg1",
    "msg2":                       "msg2",
    "msg2 enviado":               "msg2",
    "msg3":                       "msg3",
    "msg3 enviado":               "msg3",
    "msg4":                       "msg4",
    "msg5":                       "msg5",
    # Respuestas del prospecto
    "respuesta msg1":             "resp_msg1",
    "respuesta":                  "resp_msg1",   # formato antiguo junio
    "respuesta enviada":          "resp_msg1",
    "respuesta msg2":             "resp_msg2",
    "respuesta dossier":          "resp_msg2",
    "respuesta al dossier":       "resp_msg2",
    "respuesta final":            "resp_msg2",
    "respuesta msg3":             "resp_msg3",
    "respuesta msg4":             "resp_msg4",
    "respuesta msg5":             "resp_msg5",
    # SEG1 / SEG2
    "seg1":                       "seg1",
    "seg1 enviado":               "seg1",
    "seguimiento 1":              "seg1",
    "seguimiento":                "seg1",
    "respuesta seg1":             "resp_seg1",
    "seg2":                       "seg2",
    "seg2 enviado":               "seg2",
    "seguimiento 2":              "seg2",
    "respuesta seg2":             "resp_seg2",
    # Dossier (variantes junio)
    "dossier":                    "msg3",
    "dossier enviado":            "msg3",
    "confirmacion dossier":       "msg3",
    "confirmacion del dossier":   "msg3",
    "aclaracion enviada":         "msg3",
    # Conversacion completa (formato antiguo junio sin secciones)
    "conversacion":               "conversacion",
    # Cierre de conversacion
    "cierre":                     "cierre",
    "cierre dossier":             "cierre",
    "cierre final":               "cierre",
    "cierre enviado":             "cierre",
    "msg cierre":                 "cierre",
    "aviso de salida":            "cierre",
    # Seguimiento variantes
    "seguimiento conversacional":  "seg1",
    "aceptacion dossier":          "resp_msg2",
    "coordinacion de call":        "cierre",
    # MSG variantes
    "msg2 intermedio":             "msg2",
    "dossier por mail":            "msg3",
    "manejo de objecion":          "msg3",
    "correccion enviada":          "msg3",
    # Notas
    "notas":                      "notas",
    "nota":                       "notas",
}

# alias normalizado (sin tildes, lower) -> campo resultado metadata
_META_ALIASES: Dict[str, str] = {
    "fecha":   "fecha",
    "cargo":   "cargo",
    "empresa": "empresa",
    "pais":    "pais",
    "sector":  "sector",
    "estado":  "estado",
    "nombre":  "nombre",   # formato frontmatter legacy
}

# alias normalizado -> campo resultado en bloque Analisis
_ANALISIS_ALIASES: Dict[str, str] = {
    "senal humana":         "senal_humana",
    "tension profesional":  "tension",
    "tension":              "tension",
    "hipotesis":            "hipotesis",
    "angulo msg1":          "angulo_msg1",
    "angulo de msg1":       "angulo_msg1",
    "variante":             "angulo_msg1",  # alias antiguo
    "confidence":           "confidence",
    "icp":                  "icp",
}

# Transliteracion de acentos para normalizacion
_ACCENT = str.maketrans("aeiounaeiounaeiounAEIOUNAEIOUNAEIOUN",
                        "aeiounaeiounaeiounAEIOUNAEIOUNAEIOUN")
_ACCENT = str.maketrans("aeiounaeiounaeiounAEIOUNAEIOUNAEIOUN",
                        "aeiounaeiounaeiounAEIOUNAEIOUNAEIOUN")
_ACCENT = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


# ── API publica ───────────────────────────────────────────────────────────────

def parse_file(file_path: str) -> Dict:
    """
    Extrae datos crudos de un archivo .md de conversacion.
    Nunca lanza excepcion: errores van en result["parse_errors"].
    Idempotente: mismo archivo = mismo resultado.

    Campos del resultado:
      nombre, cargo, empresa, pais, sector, fecha, estado,
      senal_humana, tension, hipotesis, angulo_msg1, confidence, icp,
      msg1_texto, resp_msg1_texto, msg2_texto, resp_msg2_texto,
      msg3_texto ... msg5_texto + resp_msg3 ... resp_msg5,
      seg1_texto, seg2_texto, notas,
      conversation_text, raw_md,
      parse_warnings, parse_errors, _format_detected
    """
    result = _empty_result()
    warnings: List[str] = []
    errors: List[str] = []

    # 1. Leer archivo de forma segura
    try:
        content = _read_file_safe(file_path)
    except Exception as exc:
        errors.append(f"lectura_fallida: {exc}")
        result["parse_errors"] = errors
        return result

    result["raw_md"] = content

    # 2. Detectar formato
    fmt = _detect_format(content)
    result["_format_detected"] = fmt
    if fmt == "frontmatter":
        warnings.append(
            "formato_frontmatter: archivo con YAML frontmatter en carpeta conversaciones"
        )

    # 3. Extraer nombre desde titulo H1
    nombre, title_warn = _extract_title(content)
    if title_warn:
        warnings.append(title_warn)

    # 4. Extraer metadata (**Campo:** valor)
    meta, meta_warns = extract_metadata(content)
    warnings.extend(meta_warns)

    # nombre: H1 tiene prioridad sobre campo **Nombre:** del frontmatter
    result["nombre"] = nombre or meta.pop("nombre", "")
    for campo, valor in meta.items():
        result[campo] = valor

    # Advertir campos obligatorios vacios
    for campo in ("empresa", "sector", "fecha", "estado"):
        if not result[campo]:
            warnings.append(f"campo_vacio: {campo}")

    # 5. Splitear en secciones ## Header
    sections = extract_sections(content)

    # 6. Procesar cada seccion
    for header, body in sections:
        key = classify_section(header)

        if key == "analisis":
            analisis_data, a_warns = _extract_analisis(body)
            warnings.extend(a_warns)
            for k, v in analisis_data.items():
                result[k] = v

        elif key == "notas":
            result["notas"] = _strip_md_chrome(body).strip()

        elif key != "unknown":
            campo = f"{key}_texto"
            if campo in result:
                texto = extract_quotes(body.split("\n"))
                if not texto:
                    # Sin blockquote: guardar body limpio (formato no estandar)
                    texto = _strip_md_chrome(body).strip()
                    if texto:
                        warnings.append(
                            f"sin_blockquote: {key} — texto extraido sin marcador >"
                        )
                result[campo] = texto

        elif header.strip():
            warnings.append(f"seccion_desconocida: '{header}'")

    # 7. Construir conversation_text limpio
    result["conversation_text"] = _build_conversation_text(result)

    result["parse_warnings"] = warnings
    result["parse_errors"] = errors
    return result


def extract_metadata(content: str) -> Tuple[Dict, List[str]]:
    """
    Extrae campos de metadata de lineas **Campo:** valor.
    Primera ocurrencia de cada campo gana.
    Retorna (dict_campos, lista_warnings).
    """
    meta: Dict[str, str] = {}
    warnings: List[str] = []
    # Formato real: **Campo:** valor  (colon DENTRO de los bold markers)
    pattern = re.compile(r"^\*\*([^*:]+):\*\*\s*(.*)$")

    for line in content.split("\n"):
        m = pattern.match(line.strip())
        if not m:
            continue
        raw_key = m.group(1).strip().lower().translate(_ACCENT)
        value = m.group(2).strip()
        campo = _META_ALIASES.get(raw_key)
        if campo and campo not in meta:
            meta[campo] = value

    return meta, warnings


def extract_sections(content: str) -> List[Tuple[str, str]]:
    """
    Divide el contenido en secciones por ## Header.
    Retorna lista de (header_text, body_text).
    Contenido antes del primer ## se descarta (cabecera de metadata).
    """
    sections: List[Tuple[str, str]] = []
    current_header: str = None
    current_lines: List[str] = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_header is not None:
                sections.append((current_header, "\n".join(current_lines)))
            current_header = line[3:].strip()
            current_lines = []
        else:
            if current_header is not None:
                current_lines.append(line)

    if current_header is not None:
        sections.append((current_header, "\n".join(current_lines)))

    return sections


def classify_section(header: str) -> str:
    """
    Normaliza un header de seccion y retorna su clave interna.
    Ej: "Respuesta MSG1" -> "resp_msg1", "Analisis" -> "analisis".
    Maneja variantes con fechas y comentarios:
      "Respuesta MSG1 (02/07/26)" -> "resp_msg1"
      "MSG3 — dossier (03/07/26)" -> "msg3"
      "Respuesta MSG2 (03/07/26) — HIGH engagement" -> "resp_msg2"
    Retorna "unknown" si no hay match.
    """
    normalized = header.lower().strip().translate(_ACCENT)
    # Strip parenthetical content: (02/07/26), (HIGH engagement), etc.
    normalized = re.sub(r"\s*\(.*?\)", "", normalized)
    # Strip bare dates at end: "seguimiento 23/06/26" -> "seguimiento"
    normalized = re.sub(r"\s+\d{1,2}/\d{1,2}/\d{2,4}$", "", normalized)
    # Strip trailing — annotation (emdash y ascii dash)
    normalized = re.sub(r"\s*—.*$", "", normalized)
    normalized = re.sub(r"\s*-{1,2}\s+\w.*$", "", normalized)
    # Strip alternative after "/": "respuesta msg2 / cierre" -> "respuesta msg2"
    normalized = re.sub(r"\s*/.*$", "", normalized)
    # Normalize "respuesta a msg1" -> "respuesta msg1"
    normalized = re.sub(r"^respuesta a ", "respuesta ", normalized)
    normalized = normalized.strip()
    return _SECTION_MAP.get(normalized, "unknown")


def extract_quotes(lines: List[str]) -> str:
    """
    Extrae texto de lineas blockquote markdown (> texto).
    Lineas solitarias > se convierten en linea vacia (preserva estructura).
    """
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> "):
            result.append(stripped[2:])
        elif stripped == ">":
            result.append("")
    return "\n".join(result).strip()


def clean_text(raw_md: str) -> str:
    """
    Convierte markdown a texto plano.
    Elimina: >, **, ##, ---, frontmatter YAML.
    Conserva el contenido semantico completo.
    """
    text = raw_md

    # Remover frontmatter YAML
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5:]

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()

        # Saltar divisores ---
        if re.match(r"^-{3,}$", stripped):
            continue

        # Quitar prefijo blockquote
        if stripped.startswith("> "):
            stripped = stripped[2:]
        elif stripped == ">":
            stripped = ""

        # Quitar headers (conservar texto)
        stripped = re.sub(r"^#{1,6}\s+", "", stripped)

        # Quitar bold/italic
        stripped = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped)
        stripped = re.sub(r"\*([^*]+)\*", r"\1", stripped)

        # Quitar bullet de lista
        stripped = re.sub(r"^[-*]\s+", "", stripped)

        lines.append(stripped)

    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return result.strip()


# ── Helpers privados ──────────────────────────────────────────────────────────

def _empty_result() -> Dict:
    return {
        # Metadata cruda
        "nombre": "",
        "cargo": "",
        "empresa": "",
        "pais": "",
        "sector": "",
        "fecha": "",
        "estado": "",
        # Analisis
        "senal_humana": "",
        "tension": "",
        "hipotesis": "",
        "angulo_msg1": "",
        "confidence": "",
        "icp": "",
        # Mensajes y respuestas
        "msg1_texto": "",
        "resp_msg1_texto": "",
        "msg2_texto": "",
        "resp_msg2_texto": "",
        "msg3_texto": "",
        "resp_msg3_texto": "",
        "msg4_texto": "",
        "resp_msg4_texto": "",
        "msg5_texto": "",
        "resp_msg5_texto": "",
        "seg1_texto": "",
        "resp_seg1_texto": "",
        "seg2_texto": "",
        "resp_seg2_texto": "",
        # Cierre y formato antiguo
        "cierre_texto": "",
        "conversacion_texto": "",
        # Notas
        "notas": "",
        # Derivados
        "conversation_text": "",
        "raw_md": "",
        # Diagnostico
        "parse_warnings": [],
        "parse_errors": [],
        "_format_detected": "",
    }


def _read_file_safe(file_path: str) -> str:
    """
    Lee en UTF-8. Fallback a latin-1 si falla la decodificacion.
    No hace retry — el siguiente build lo reintentara.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as fh:
            return fh.read()


def _detect_format(content: str) -> str:
    """
    'frontmatter': empieza con YAML --- (archivos de memoria en carpeta conversaciones)
    'standard': formato normal con # Nombre y **Campo:** valor
    """
    if content.startswith("---\n") or content.startswith("---\r\n"):
        first_end = content.find("\n---\n", 3)
        if first_end != -1:
            first_block = content[4:first_end]
            if re.search(r"^(name|description|metadata)\s*:", first_block, re.MULTILINE):
                return "frontmatter"
    return "standard"


def _extract_title(content: str) -> Tuple[str, str]:
    """
    Extrae nombre desde el primer # H1 (excluye ## y ###).
    Retorna (nombre, warning). Warning es "" si ok.
    """
    for line in content.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip(), ""
    return "", "sin_titulo_h1: nombre no encontrado en encabezado H1"


def _extract_analisis(body: str) -> Tuple[Dict, List[str]]:
    """
    Extrae sub-campos del bloque ## Analisis.
    Formato esperado: - **Campo:** valor (puede ser multilinea)
    """
    result: Dict[str, str] = {k: "" for k in (
        "senal_humana", "tension", "hipotesis",
        "angulo_msg1", "confidence", "icp",
    )}
    warnings: List[str] = []
    # Formato real: - **Campo:** valor  (colon DENTRO de los bold markers)
    pattern = re.compile(r"^[-*]\s*\*\*([^*:]+):\*\*\s*(.*)$")

    current_field: str = None
    current_lines: List[str] = []

    def _flush() -> None:
        if current_field and current_lines:
            result[current_field] = " ".join(current_lines).strip()

    for line in body.split("\n"):
        m = pattern.match(line.strip())
        if m:
            _flush()
            raw_key = m.group(1).strip().lower().translate(_ACCENT)
            current_field = _ANALISIS_ALIASES.get(raw_key)
            first_val = m.group(2).strip()
            current_lines = [first_val] if first_val else []
        elif current_field and line.strip() and not line.strip().startswith("##"):
            stripped = line.strip()
            # Saltar separadores --- (estan al final del bloque Analisis)
            if re.match(r"^-{3,}$", stripped):
                continue
            # Continuacion multilinea del campo actual
            cleaned = re.sub(r"^[-*]\s+", "", stripped)
            current_lines.append(cleaned)

    _flush()
    return result, warnings


def _strip_md_chrome(text: str) -> str:
    """Quita >, **, ##, --- del texto pero conserva el contenido."""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if re.match(r"^-{3,}$", stripped):
            continue
        if stripped.startswith("> "):
            stripped = stripped[2:]
        elif stripped == ">":
            stripped = ""
        stripped = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped)
        stripped = re.sub(r"^#{1,6}\s+", "", stripped)
        lines.append(stripped)
    return "\n".join(lines)


def _build_conversation_text(parsed: Dict) -> str:
    """
    Construye texto limpio estructurado para embeddings futuros.
    Formato: cabecera de contexto + secuencia etiquetada de mensajes.
    """
    parts: List[str] = []

    # Contexto del prospecto
    for field, label in (
        ("nombre",  "NOMBRE"),
        ("empresa", "EMPRESA"),
        ("cargo",   "CARGO"),
        ("sector",  "SECTOR"),
        ("pais",    "PAIS"),
    ):
        val = parsed.get(field, "").strip()
        if val:
            parts.append(f"[{label}: {val}]")

    # Senales del analisis
    for field, label in (
        ("senal_humana", "SENAL"),
        ("hipotesis",    "HIPOTESIS"),
    ):
        val = parsed.get(field, "").strip()
        if val:
            parts.append(f"[{label}: {val}]")

    parts.append("")  # separador

    # Secuencia de mensajes
    sequence = (
        ("msg1_texto",      "MSG1"),
        ("resp_msg1_texto", "RESPUESTA_MSG1"),
        ("msg2_texto",      "MSG2"),
        ("resp_msg2_texto", "RESPUESTA_MSG2"),
        ("msg3_texto",      "MSG3"),
        ("resp_msg3_texto", "RESPUESTA_MSG3"),
        ("msg4_texto",      "MSG4"),
        ("resp_msg4_texto", "RESPUESTA_MSG4"),
        ("msg5_texto",      "MSG5"),
        ("resp_msg5_texto", "RESPUESTA_MSG5"),
        ("seg1_texto",      "SEG1"),
        ("seg2_texto",      "SEG2"),
    )
    for field, label in sequence:
        val = parsed.get(field, "").strip()
        if val:
            parts.append(f"[{label}]")
            parts.append(val)
            parts.append("")

    # Notas
    notas = parsed.get("notas", "").strip()
    if notas:
        parts.append("[NOTAS]")
        parts.append(notas)

    return "\n".join(parts).strip()
