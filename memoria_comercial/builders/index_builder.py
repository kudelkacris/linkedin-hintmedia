"""
index_builder.py — IDs permanentes de conversaciones + escritura conv_XXXXXX.json.

Reglas de resolución de ID:
  - path match en registry       → mismo conv_id
  - hash match sin path match    → archivo renombrado, conservar conv_id, actualizar path
  - ninguno                      → nuevo archivo, incrementar last_id, registrar

JSON es la fuente de verdad. CSV es exportación derivada.
"""
import dataclasses
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    ID_REGISTRY_PATH, CONVERSATIONS_DIR, CONVERSATIONS_INDEX_PATH,
    CONV_ID_PREFIX, CONV_ID_PADDING, SCHEMA_VERSION,
)
from schemas.conversation import ConversationRecord


def load_registry() -> Dict:
    if os.path.exists(ID_REGISTRY_PATH):
        try:
            with open(ID_REGISTRY_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict) and "entries" in data:
                    return data
        except Exception:
            pass
    return {"schema_version": SCHEMA_VERSION, "last_id": 0, "entries": {}}


def save_registry(registry: Dict) -> None:
    os.makedirs(os.path.dirname(ID_REGISTRY_PATH), exist_ok=True)
    with open(ID_REGISTRY_PATH, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, ensure_ascii=False, indent=2)


def resolve_id(file_path: str, file_hash: str, registry: Dict) -> str:
    """
    Retorna conv_id para este archivo. Puede modificar registry.
    file_path: relativo a LINKEDIN_ROOT con forward slashes.
    file_hash: "sha256:..." del fingerprinter.
    """
    entries = registry["entries"]

    # 1. Path match — caso normal
    if file_path in entries:
        entries[file_path]["file_hash"] = file_hash
        return entries[file_path]["conv_id"]

    # 2. Hash match — archivo renombrado o movido
    for stored_path, entry in list(entries.items()):
        if entry.get("file_hash") == file_hash:
            new_entry = {"conv_id": entry["conv_id"], "file_hash": file_hash}
            entries[file_path] = new_entry
            del entries[stored_path]
            return entry["conv_id"]

    # 3. Nuevo archivo
    registry["last_id"] += 1
    conv_id = format_conv_id(registry["last_id"])
    entries[file_path] = {"conv_id": conv_id, "file_hash": file_hash}
    return conv_id


def format_conv_id(n: int) -> str:
    return f"{CONV_ID_PREFIX}{str(n).zfill(CONV_ID_PADDING)}"


def save_conversation(record: ConversationRecord) -> None:
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    path = os.path.join(CONVERSATIONS_DIR, f"{record.conversation_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dataclasses.asdict(record), fh, ensure_ascii=False, indent=2)


def build_index(records: List[ConversationRecord]) -> None:
    """Escribe conversations_index.json — índice liviano sin textos largos."""
    index = []
    for r in sorted(records, key=lambda x: x.conversation_id):
        index.append({
            "conversation_id": r.conversation_id,
            "contact_id": r.contact_id,
            "source_file": r.source_file,
            "nombre": r.metadata.nombre,
            "empresa": r.metadata.empresa,
            "pais": r.metadata.pais,
            "sector": r.normalized.sector,
            "seniority": r.normalized.seniority,
            "stage": r.normalized.stage,
            "resultado_final": r.normalized.resultado_final,
            "engagement_level": r.normalized.engagement_level,
            "variante_msg1": r.normalized.variante_msg1,
            "respondio_msg1": r.conversation.respondio_msg1,
            "dossier_enviado": r.conversation.dossier_enviado,
            "call_agendada": r.conversation.call_agendada,
            "fecha": r.metadata.fecha,
        })

    os.makedirs(os.path.dirname(CONVERSATIONS_INDEX_PATH), exist_ok=True)
    with open(CONVERSATIONS_INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump({"total": len(index), "records": index}, fh, ensure_ascii=False, indent=2)
