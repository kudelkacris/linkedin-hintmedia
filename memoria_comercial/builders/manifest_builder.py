"""
manifest_builder.py — Construye manifest.json global.

Puerta de entrada de toda la Memoria Comercial.
Incluye totales, cobertura de campos, estadísticas de build y versiones.
"""
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MANIFEST_PATH, SCHEMA_VERSION, PARSER_VERSION, DATASET_VERSION
from schemas.conversation import ConversationRecord


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def compute_field_coverage(records: List[ConversationRecord]) -> Dict:
    """Fracción de records con valor no-vacío y no-DESCONOCIDO por campo clave."""
    if not records:
        return {}
    n = len(records)
    _empty = {"DESCONOCIDO", ""}

    def filled(v) -> bool:
        return str(v) not in _empty

    return {
        "nombre":       round(sum(1 for r in records if filled(r.metadata.nombre)) / n, 3),
        "empresa":      round(sum(1 for r in records if filled(r.metadata.empresa)) / n, 3),
        "cargo":        round(sum(1 for r in records if filled(r.metadata.cargo)) / n, 3),
        "pais":         round(sum(1 for r in records if filled(r.metadata.pais)) / n, 3),
        "sector":       round(sum(1 for r in records if filled(r.normalized.sector.value)) / n, 3),
        "seniority":    round(sum(1 for r in records if filled(r.normalized.seniority.value)) / n, 3),
        "stage":        round(sum(1 for r in records if r.normalized.stage > 0) / n, 3),
        "msg1_texto":   round(sum(1 for r in records if filled(r.conversation.msg1_texto)) / n, 3),
        "senal_humana": round(sum(1 for r in records if filled(r.signals.señal_humana)) / n, 3),
        "engagement":   round(sum(1 for r in records if filled(r.normalized.engagement_level.value)) / n, 3),
        "variante":     round(sum(1 for r in records if r.normalized.variante_msg1.value != "DESCONOCIDA") / n, 3),
    }


def build_manifest(
    records: List[ConversationRecord],
    errors: List[Dict],
    build_mode: str,
    build_start: float,
    incremental_stats: Dict,
) -> None:
    now = _utc_now()
    duration = round(time.time() - build_start, 2)

    folder_ctr: Counter = Counter()
    stage_ctr: Counter = Counter()
    resultado_ctr: Counter = Counter()
    with_warnings = 0
    with_errors = 0

    for r in records:
        folder_ctr[r.source.month_folder] += 1
        stage_ctr[r.normalized.stage] += 1
        resultado_ctr[r.normalized.resultado_final.value] += 1
        if r.quality.parse_warnings:
            with_warnings += 1
        if r.quality.parse_errors:
            with_errors += 1

    total = len(records)
    manifest = {
        "schema_version":         SCHEMA_VERSION,
        "parser_version":         PARSER_VERSION,
        "dataset_version":        DATASET_VERSION,
        "build_date":             now,
        "build_mode":             build_mode,
        "build_duration_seconds": duration,
        "totals": {
            "total_conversations": total,
            "clean":               total - with_warnings - with_errors,
            "with_warnings":       with_warnings,
            "with_errors":         with_errors,
            "errors_fatal":        len(errors),
        },
        "by_folder":    dict(sorted(folder_ctr.items())),
        "by_stage":     {str(k): v for k, v in sorted(stage_ctr.items())},
        "by_resultado": dict(resultado_ctr.most_common()),
        "field_coverage": compute_field_coverage(records),
        "incremental":  incremental_stats or {},
    }

    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
