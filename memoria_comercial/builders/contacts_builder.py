"""
contacts_builder.py — Nivel 1 de la Memoria Comercial: CONTACTS.

Fuente: historial.json (solo lectura, nunca modifica).
Output: ctc_XXXXXX.json en dataset/contacts/ + contacts_index.json

Linking contacts ↔ conversations:
  El caller (run.py) construye primero las conversaciones,
  luego pasa el mapa slug→conv_id para que contacts_builder
  setee tiene_md y conversation_id antes de guardar.
"""
import dataclasses
import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    HISTORIAL_PATH, CONTACTS_DIR, CONTACTS_INDEX_PATH, CONTACTS_REGISTRY_PATH,
    CONTACT_ID_PREFIX, CONTACT_ID_PADDING, SCHEMA_VERSION,
)
from schemas.contact import ContactRecord
from schemas.fields import Sector, Seniority


def load_historial() -> List[Dict]:
    """Carga historial.json. Solo lectura — nunca modifica."""
    with open(HISTORIAL_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_contacts_registry() -> Dict:
    if os.path.exists(CONTACTS_REGISTRY_PATH):
        try:
            with open(CONTACTS_REGISTRY_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict) and "entries" in data:
                    return data
        except Exception:
            pass
    return {"schema_version": SCHEMA_VERSION, "last_id": 0, "entries": {}}


def save_contacts_registry(registry: Dict) -> None:
    os.makedirs(os.path.dirname(CONTACTS_REGISTRY_PATH), exist_ok=True)
    with open(CONTACTS_REGISTRY_PATH, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, ensure_ascii=False, indent=2)


def resolve_contact_id(historial_slug: str, registry: Dict) -> str:
    """
    Retorna ctc_id para este slug.
    Si ya existe en el registry → mismo ctc_id.
    Si es nuevo → ctc_id incremental + registro.
    """
    entries = registry["entries"]
    if historial_slug in entries:
        return entries[historial_slug]["ctc_id"]
    registry["last_id"] += 1
    ctc_id = format_contact_id(registry["last_id"])
    entries[historial_slug] = {"ctc_id": ctc_id}
    return ctc_id


def format_contact_id(n: int) -> str:
    return f"{CONTACT_ID_PREFIX}{str(n).zfill(CONTACT_ID_PADDING)}"


def normalize_contact(raw: Dict, ctc_id: str, created_at: str) -> ContactRecord:
    """
    Convierte entrada del historial.json en ContactRecord tipado.
    tiene_md y conversation_id quedan en False/None — el caller los setea
    después de construir el mapa slug→conv_id de las conversaciones.
    """
    from builders.normalizer import detect_sector, detect_seniority

    # historial usa 'name' (nuevos) o 'nombre' (14 entradas legacy)
    nombre = raw.get("name") or raw.get("nombre", "")
    empresa = raw.get("empresa", "")
    cargo = raw.get("cargo", "")
    pais = raw.get("pais", "")
    sector_raw = raw.get("sector", "")

    stage_raw = raw.get("stage", 1)
    try:
        stage = int(stage_raw)
    except (ValueError, TypeError):
        stage = 1

    stage_texto = raw.get("estado", "")
    fecha = raw.get("fecha") or raw.get("date", "")
    email = raw.get("email") or None

    sector_norm_val = detect_sector(empresa, cargo, sector_raw)
    seniority_val = detect_seniority(cargo)

    return ContactRecord(
        contact_id=ctc_id,
        schema_version=SCHEMA_VERSION,
        created_at=created_at,
        updated_at=created_at,
        nombre=nombre,
        empresa=empresa,
        cargo=cargo,
        pais=pais,
        sector_raw=sector_raw,
        stage=stage,
        stage_texto=stage_texto,
        fecha=fecha,
        email=email,
        sector_norm=Sector(sector_norm_val),
        seniority=Seniority(seniority_val),
        tiene_md=False,
        conversation_id=None,
        historial_slug=raw.get("id", ""),
    )


_ACCENT = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def norm_name(s: str) -> str:
    """Normaliza nombre: minúsculas + sin tildes + espacios colapsados."""
    import re as _re
    return _re.sub(r"\s+", " ", (s or "").lower().translate(_ACCENT).strip())


def detect_tiene_md(nombre: str, historial_slug: str, md_names: set) -> bool:
    """md_names: set de norm_name(md_nombre) precalculado por el caller."""
    return norm_name(nombre) in md_names


def save_contact(record: ContactRecord) -> None:
    os.makedirs(CONTACTS_DIR, exist_ok=True)
    path = os.path.join(CONTACTS_DIR, f"{record.contact_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dataclasses.asdict(record), fh, ensure_ascii=False, indent=2)


def build_contacts_index(records: List[ContactRecord]) -> None:
    """Escribe contacts_index.json — índice liviano para queries rápidas."""
    index = []
    for r in sorted(records, key=lambda x: x.contact_id):
        index.append({
            "contact_id": r.contact_id,
            "historial_slug": r.historial_slug,
            "nombre": r.nombre,
            "empresa": r.empresa,
            "cargo": r.cargo,
            "pais": r.pais,
            "sector_norm": r.sector_norm,
            "seniority": r.seniority,
            "stage": r.stage,
            "stage_texto": r.stage_texto,
            "tiene_md": r.tiene_md,
            "conversation_id": r.conversation_id,
            "fecha": r.fecha,
            "email": r.email,
        })

    os.makedirs(os.path.dirname(CONTACTS_INDEX_PATH), exist_ok=True)
    with open(CONTACTS_INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump({"total": len(index), "records": index}, fh, ensure_ascii=False, indent=2)
