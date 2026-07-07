"""
report_builder.py — HITO 6: reportes de cobertura y calidad del dataset.

coverage_report.md: totales, % por campo, por folder, por stage, errores.
quality_report.md: inconsistencias detectadas sin IA (7 checks).
"""
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MANIFEST_PATH, CONVERSATIONS_DIR, CONTACTS_INDEX_PATH,
    COVERAGE_REPORT_PATH, QUALITY_REPORT_PATH, REPORTS_DIR,
)

_ACCENT = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().translate(_ACCENT).strip())


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _load_manifest() -> Dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_all_conversations() -> List[Dict]:
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
            pass
    return records


def _load_contacts_index() -> Dict:
    if not os.path.exists(CONTACTS_INDEX_PATH):
        return {"total": 0, "records": []}
    with open(CONTACTS_INDEX_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_coverage_report() -> None:
    manifest = _load_manifest()
    records = _load_all_conversations()
    contacts = _load_contacts_index()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    totals = manifest.get("totals", {})
    field_cov = manifest.get("field_coverage", {})
    by_folder = manifest.get("by_folder", {})
    by_stage = manifest.get("by_stage", {})
    by_resultado = manifest.get("by_resultado", {})
    errors_list = manifest.get("incremental", {}).get("errors", []) or []

    total_conv = totals.get("conversations", len(records)) or 1
    total_ctc = contacts["total"]
    ctc_con_md = sum(1 for r in contacts["records"] if r.get("tiene_md"))

    # Campos ordenados de menor a mayor cobertura (más huecos primero)
    sorted_fields = sorted(field_cov.items(), key=lambda x: x[1])

    lines = [
        "# Coverage Report",
        "",
        f"_Generado: {now}_",
        "",
        "---",
        "",
        "## Totales",
        "",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Conversaciones procesadas | {total_conv} |",
        f"| Contactos (historial.json) | {total_ctc} |",
        f"| Contactos con .md vinculado | {ctc_con_md} ({_pct(ctc_con_md / total_ctc if total_ctc else 0)}) |",
        f"| Contactos solo en historial | {total_ctc - ctc_con_md} |",
        f"| Errores de parse | {totals.get('errors', len(errors_list))} |",
        "",
        "---",
        "",
        "## Cobertura por Campo",
        "",
        "_Ordenado por cobertura ascendente — mas huecos arriba_",
        "",
        "| Campo | Cobertura | Llenos | Huecos |",
        "|-------|-----------|--------|--------|",
    ]

    for field, cov in sorted_fields:
        filled = round(cov * total_conv)
        gaps = total_conv - filled
        lines.append(f"| {field} | {_pct(cov)} | {filled} | {gaps} |")

    lines += [
        "",
        "---",
        "",
        "## Por Carpeta (mes)",
        "",
        "| Carpeta | Conversaciones |",
        "|---------|---------------|",
    ]
    for folder, count in sorted(by_folder.items()):
        lines.append(f"| {folder} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## Por Stage",
        "",
        "| Stage | Conversaciones | % |",
        "|-------|---------------|---|",
    ]
    for stage, count in sorted(by_stage.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 99):
        lines.append(f"| {stage} | {count} | {_pct(count / total_conv)} |")

    lines += [
        "",
        "---",
        "",
        "## Por Resultado",
        "",
        "| Resultado | Conversaciones | % |",
        "|-----------|---------------|---|",
    ]
    for res, count in sorted(by_resultado.items(), key=lambda x: -x[1]):
        label = res if res else "pendiente"
        lines.append(f"| {label} | {count} | {_pct(count / total_conv)} |")

    if errors_list:
        lines += [
            "",
            "---",
            "",
            f"## Archivos con Errores ({len(errors_list)})",
            "",
        ]
        for err in errors_list[:50]:
            lines.append(f"- `{err.get('file', '?')}`: {err.get('error', '?')}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(COVERAGE_REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def build_quality_report() -> None:
    records = _load_all_conversations()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    issues: List[Tuple[str, str, str]] = []  # (conv_id, nombre, descripcion)
    seen_nombres: Dict[str, str] = {}

    for d in records:
        conv_id = d.get("conversation_id", "?")
        meta = d.get("metadata") or {}
        norm = d.get("normalized") or {}
        conv = d.get("conversation") or {}
        qual = d.get("quality") or {}

        nombre = meta.get("nombre", "")
        stage = norm.get("stage", 0)
        respondio_msg1 = conv.get("respondio_msg1", False)
        resp_txt = conv.get("respuesta_msg1_texto", "")
        dossier_enviado = conv.get("dossier_enviado", False)
        engagement = norm.get("engagement_level", "")
        fecha = meta.get("fecha", "")
        confidence = qual.get("confidence_score", 0)

        n_key = _norm(nombre)

        # 1. Nombre duplicado entre archivos
        if n_key:
            if n_key in seen_nombres:
                issues.append((conv_id, nombre, f"Nombre duplicado con {seen_nombres[n_key]}"))
            else:
                seen_nombres[n_key] = conv_id

        # 2. Texto respuesta MSG1 presente pero flag False
        if resp_txt and not respondio_msg1:
            issues.append((conv_id, nombre, "resp_msg1_texto presente pero respondio_msg1=False"))

        # 3. Dossier enviado pero stage < 3
        if dossier_enviado and stage < 3:
            issues.append((conv_id, nombre, f"dossier_enviado=True pero stage={stage}"))

        # 4. Stage 3+ pero dossier_enviado=False
        if stage >= 3 and not dossier_enviado:
            issues.append((conv_id, nombre, f"stage={stage} pero dossier_enviado=False"))

        # 5. Engagement HIGH con respuesta muy corta
        if engagement == "HIGH" and resp_txt and len(resp_txt.strip()) < 15:
            issues.append((conv_id, nombre, f"engagement=HIGH con respuesta de {len(resp_txt)} chars"))

        # 6. Sin fecha
        if not fecha:
            issues.append((conv_id, nombre, "Sin fecha"))

        # 7. Confidence muy bajo
        if isinstance(confidence, (int, float)) and confidence < 0.25:
            issues.append((conv_id, nombre, f"confidence_score={confidence:.2f} — revisar manualmente"))

    # Agrupar por tipo
    issue_types: Dict[str, int] = {}
    for _, _, desc in issues:
        key = desc.split("—")[0].split("pero")[0].strip()
        issue_types[key] = issue_types.get(key, 0) + 1

    lines = [
        "# Quality Report",
        "",
        f"_Generado: {now}_",
        "",
        "---",
        "",
        "## Resumen",
        "",
        f"- Conversaciones analizadas: {len(records)}",
        f"- Inconsistencias detectadas: {len(issues)}",
        "",
        "### Por tipo",
        "",
        "| Tipo | Cantidad |",
        "|------|----------|",
    ]
    for itype, count in sorted(issue_types.items(), key=lambda x: -x[1]):
        lines.append(f"| {itype} | {count} |")

    lines += [
        "",
        "---",
        "",
        f"## Detalle ({len(issues)} inconsistencias)",
        "",
    ]

    if not issues:
        lines.append("_Sin inconsistencias detectadas._")
    else:
        lines += [
            "| Conv ID | Nombre | Problema |",
            "|---------|--------|----------|",
        ]
        for conv_id, nombre, desc in issues:
            nb = nombre.replace("|", "\\|")
            dc = desc.replace("|", "\\|")
            lines.append(f"| {conv_id} | {nb} | {dc} |")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(QUALITY_REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
