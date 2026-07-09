"""
dataset/reader.py — Read-only access to conversaciones/*.md files.

Single responsibility: find and parse a prospect .md file.
Never writes. Never modifies. Never calls APIs.
"""
import re
from pathlib import Path
from typing import Optional
from datetime import date

_LINKEDIN_ROOT = Path(__file__).parent.parent.parent
_CONV_DIRS = [
    _LINKEDIN_ROOT / "conversaciones" / "julio",
    _LINKEDIN_ROOT / "conversaciones" / "junio",
]
_TODAY = date.today()

# Seniority keyword matching — ordered most-specific first
_SENIORITY_KEYWORDS = [
    ("CEO",        ["ceo", "chief executive", "director general", "director ejecutivo", "fundador", "co-founder", "founder"]),
    ("DIRECTOR",   ["director", "vp ", "vice president", "vicepresidente", "head of", "gerente general"]),
    ("MANAGER",    ["manager", "gerente", "jefe de", "lead ", "líder", "lider", "supervisor"]),
    ("SPECIALIST", ["specialist", "analista", "analyst", "associate", "coordinator", "coordinador",
                    "ejecutivo", "consultor", "asesor", "técnico", "tecnico", "ingeniero"]),
]

# Maps fragments in sector strings from .md → canonical key in sectors.json
_SECTOR_FRAGMENTS = [
    ("farmac",      "Farmacéutico"),
    ("salud",       "Farmacéutico"),
    ("energ",       "Energía"),
    ("educac",      "Educación"),
    ("tecnol",      "Tecnología"),
    ("software",    "Tecnología"),
    ("retail",      "Retail/Consumo"),
    ("consumo",     "Retail/Consumo"),
    ("miner",       "Minería"),
    ("consultor",   "Consultoría/Legal"),
    ("legal",       "Consultoría/Legal"),
    ("seguro",      "Seguros/Finanzas"),
    ("finanza",     "Seguros/Finanzas"),
    ("banco",       "Seguros/Finanzas"),
    ("turismo",     "Turismo/Hotelería"),
    ("hotel",       "Turismo/Hotelería"),
    ("agencia",     "Agencia/Marketing"),
    ("marketing",   "Agencia/Marketing"),
]

# Maps estado fragments → stage string
_ESTADO_TO_STAGE = [
    (["reunión agendada", "reunion agendada", "meeting agendado"],  "6"),
    (["seg1 enviado", "seguimiento 1"],                             "4"),
    (["dossier enviado", "dossier confirmado", "dossier por mail"], "3"),
    (["msg2 enviado"],                                              "2"),
    (["msg1 enviado"],                                              "1"),
]


def find_and_read(prospect_name: str) -> Optional[dict]:
    """Find the .md file for a prospect and return parsed data. None if not found."""
    file_path = _find_file(prospect_name)
    if not file_path:
        return None
    return _parse_md(file_path)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _find_file(name: str) -> Optional[Path]:
    slug = _to_slug(name)
    first = _to_slug(name.split()[0]) if name.split() else slug
    for d in _CONV_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            stem = f.stem
            if stem == slug or slug in stem or stem.startswith(first):
                return f
    return None


def _to_slug(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [('á','a'),('à','a'),('é','e'),('è','e'),('í','i'),
                     ('ì','i'),('ó','o'),('ò','o'),('ú','u'),('ù','u'),('ñ','n')]:
        text = text.replace(src, dst)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'\s+', '-', text).strip('-')


def _parse_md(file_path: Path) -> dict:
    text = file_path.read_text(encoding='utf-8')
    lines = text.split('\n')

    result: dict = {
        "file_path":         str(file_path),
        "name":              None,
        "cargo":             None,
        "cargo_seniority":   "OTHER",
        "empresa":           None,
        "sector":            None,
        "pais":              None,
        "estado":            None,
        "stage":             None,
        "msg2_angle":        None,
        "dossier_date_str":  None,
        "days_since_dossier": None,
        "msg2_text":         None,
        "prospect_responses": [],
    }

    # Name from first H1
    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            result["name"] = line[2:].strip()
            break

    # Frontmatter fields
    _FIELD_MAP = {
        "**cargo:**":  "cargo",
        "**empresa:**": "empresa",
        "**sector:**":  "sector",
        "**país:**":    "pais",
        "**estado:**":  "estado",
    }
    for line in lines:
        low = line.lower().strip()
        for key, field in _FIELD_MAP.items():
            if low.startswith(key):
                val = re.sub(r'\*\*[^*]+\*\*\s*:?\s*', '', line, count=1).strip()
                result[field] = val or None

    if result["sector"]:
        result["sector"] = _normalize_sector(result["sector"])
    if result["cargo"]:
        result["cargo_seniority"] = _map_seniority(result["cargo"])
    if result["estado"]:
        result["stage"] = _map_stage(result["estado"])

    # MSG2 text (first quoted block under ## MSG2)
    msg2_lines, in_msg2 = [], False
    for line in lines:
        if re.match(r'^## MSG2', line):
            in_msg2 = True
            continue
        if in_msg2:
            if line.startswith('## '):
                break
            if line.startswith('> '):
                msg2_lines.append(line[2:].strip())
    result["msg2_text"] = ' '.join(msg2_lines) or None

    # Prospect responses (all > blocks under ## Respuesta / ## Confirmación)
    responses, in_resp = [], False
    for line in lines:
        if re.match(r'^## (Respuesta|Confirmaci)', line):
            in_resp = True
            continue
        if in_resp:
            if line.startswith('## '):
                in_resp = False
                continue
            if line.startswith('> '):
                responses.append(line[2:].strip())
    result["prospect_responses"] = responses

    # Dossier date
    dossier_date = _extract_dossier_date(text)
    if dossier_date:
        result["dossier_date_str"] = str(dossier_date)
        result["days_since_dossier"] = (_TODAY - dossier_date).days

    return result


def _extract_dossier_date(text: str) -> Optional[date]:
    """Best-effort extraction of dossier send date from .md text."""
    dossier_lines = [l for l in text.split('\n')
                     if 'dossier' in l.lower() or 'mandado' in l.lower()]
    for line in dossier_lines:
        # DD/MM/YY or DD/MM/YYYY
        m = re.search(r'(\d{1,2})/(\d{2})/(\d{2,4})', line)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            try:
                return date(y, mo, d)
            except ValueError:
                pass
        # "el 29/06" (no year)
        m = re.search(r'el (\d{1,2})/(\d{2})\b', line)
        if m:
            d, mo = int(m.group(1)), int(m.group(2))
            try:
                return date(_TODAY.year, mo, d)
            except ValueError:
                pass
    return None


def _normalize_sector(sector: str) -> str:
    low = sector.lower()
    for fragment, canonical in _SECTOR_FRAGMENTS:
        if fragment in low:
            return canonical
    return sector


def _map_seniority(cargo: str) -> str:
    low = cargo.lower()
    for seniority, keywords in _SENIORITY_KEYWORDS:
        for kw in keywords:
            if kw in low:
                return seniority
    return "OTHER"


def _map_stage(estado: str) -> Optional[str]:
    low = estado.lower()
    for signals, stage in _ESTADO_TO_STAGE:
        if any(s in low for s in signals):
            return stage
    return None
