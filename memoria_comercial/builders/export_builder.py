"""
export_builder.py — Genera conversations.csv desde conv_XXXXXX.json.

JSON es la fuente de verdad. CSV es exportación derivada.
Encoding utf-8-sig (BOM) para compatibilidad con Excel en Windows.
No incluye raw_md — demasiado largo para una columna CSV.
"""
import csv
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONVERSATIONS_DIR, CSV_PATH

_CSV_COLUMNS = [
    # Identificación
    "conversation_id", "contact_id", "source_file", "fingerprint",
    "created_at", "updated_at", "schema_version", "build_date",
    # Source
    "month_folder",
    # Metadata
    "nombre", "empresa", "cargo", "pais", "fecha", "estado_texto",
    # Normalized
    "sector", "seniority", "tipo_decisor", "stage",
    "resultado_final", "objecion_principal", "engagement_level", "variante_msg1",
    # Conversation flags
    "respondio_msg1", "dossier_enviado", "seg1_enviado", "seg2_enviado",
    "call_agendada", "cliente_cerrado",
    # Quality
    "confidence_score",
    # Signals
    "senal_humana", "hipotesis", "notas",
    # Textos clave (no raw_md)
    "msg1_texto", "resp_msg1_texto", "msg2_texto",
]


def load_all_records() -> List[Dict]:
    """Carga todos los conv_XXXXXX.json ordenados por conv_id."""
    if not os.path.exists(CONVERSATIONS_DIR):
        return []
    records = []
    for fname in sorted(os.listdir(CONVERSATIONS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(CONVERSATIONS_DIR, fname), "r", encoding="utf-8") as fh:
                records.append(json.load(fh))
        except Exception:
            continue
    return records


def flatten_record(d: Dict) -> Dict:
    """Convierte ConversationRecord anidado en dict plano para CSV."""
    src = d.get("source") or {}
    meta = d.get("metadata") or {}
    norm = d.get("normalized") or {}
    conv = d.get("conversation") or {}
    qual = d.get("quality") or {}
    sig = d.get("signals") or {}

    return {
        "conversation_id": d.get("conversation_id", ""),
        "contact_id":      d.get("contact_id", ""),
        "source_file":     d.get("source_file", ""),
        "fingerprint":     d.get("fingerprint", ""),
        "created_at":      d.get("created_at", ""),
        "updated_at":      d.get("updated_at", ""),
        "schema_version":  d.get("schema_version", ""),
        "build_date":      d.get("build_date", ""),
        "month_folder":    src.get("month_folder", ""),
        "nombre":          meta.get("nombre", ""),
        "empresa":         meta.get("empresa", ""),
        "cargo":           meta.get("cargo", ""),
        "pais":            meta.get("pais", ""),
        "fecha":           meta.get("fecha", ""),
        "estado_texto":    meta.get("estado_texto", ""),
        "sector":          norm.get("sector", ""),
        "seniority":       norm.get("seniority", ""),
        "tipo_decisor":    norm.get("tipo_decisor", ""),
        "stage":           norm.get("stage", ""),
        "resultado_final": norm.get("resultado_final", ""),
        "objecion_principal": norm.get("objecion_principal", ""),
        "engagement_level": norm.get("engagement_level", ""),
        "variante_msg1":   norm.get("variante_msg1", ""),
        "respondio_msg1":  conv.get("respondio_msg1", False),
        "dossier_enviado": conv.get("dossier_enviado", False),
        "seg1_enviado":    conv.get("seg1_enviado", False),
        "seg2_enviado":    conv.get("seg2_enviado", False),
        "call_agendada":   conv.get("call_agendada", False),
        "cliente_cerrado": conv.get("cliente_cerrado", False),
        "confidence_score": qual.get("confidence_score", 0),
        "senal_humana":    sig.get("señal_humana", ""),
        "hipotesis":       sig.get("hipotesis", ""),
        "notas":           sig.get("notas", ""),
        "msg1_texto":      conv.get("msg1_texto", ""),
        "resp_msg1_texto": conv.get("respuesta_msg1_texto", ""),
        "msg2_texto":      conv.get("msg2_texto", ""),
    }


def export_csv() -> int:
    """Exporta conversations.csv. Retorna cantidad de filas escritas."""
    records = load_all_records()
    if not records:
        return 0

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(flatten_record(rec))

    return len(records)
