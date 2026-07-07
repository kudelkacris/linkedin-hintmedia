"""
run.py — Memoria Comercial: punto de entrada unico.

Uso:
    python run.py --full      Procesado completo desde cero
    python run.py --update    Solo archivos con hash cambiado
    python run.py --export    Regenera CSV desde JSON (sin reprocesar)
    python run.py --report    Regenera reportes (sin reprocesar)

Completamente independiente del programa principal.
Puede borrarse la carpeta memoria_comercial/ y el sistema sigue igual.
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    PARSER_VERSION, SCHEMA_VERSION, DATASET_VERSION,
    BUILD_LOG_PATH, CONVERSACIONES_ROOT, CSV_PATH, MANIFEST_PATH,
)

# ── Logging ───────────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    os.makedirs(os.path.dirname(BUILD_LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(BUILD_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_full() -> None:
    """Full rebuild: crawl + fingerprint + parse + normalize + index + manifest + export."""
    import json
    from builders.crawler import discover_files, report_discovery, print_report
    from builders.fingerprinter import compute_fingerprint
    from builders.parser import parse_file
    from config import CACHE_PATH, CONVERSACIONES_ROOT

    t0 = time.time()
    logging.info(f"Memoria Comercial v{PARSER_VERSION} — FULL BUILD iniciado")
    logging.info(f"Fuente: {CONVERSACIONES_ROOT}")

    # ── HITO 2: Crawl ────────────────────────────────────────────────────────
    files = discover_files()
    report = report_discovery(files)
    print_report(report)
    logging.info(
        f"Crawl: {report['total']} archivos — errores: {len(report['errors'])}"
    )

    # ── HITO 3: Parse ────────────────────────────────────────────────────────
    t_parse = time.time()
    parsed_all = {}
    parse_stats = {
        "total": 0, "ok": 0, "con_warnings": 0, "con_errors": 0,
        "sin_empresa": 0, "sin_cargo": 0, "con_analisis": 0,
        "con_respuesta_msg1": 0, "con_msg2": 0, "con_seg1": 0,
    }

    for file_path in files:
        rel = os.path.relpath(file_path, os.path.dirname(CONVERSACIONES_ROOT))
        fp_data = compute_fingerprint(file_path)
        parsed = parse_file(file_path)

        parsed["_source_file"] = rel.replace("\\", "/")
        parsed["_fingerprint"] = fp_data["file_hash"]
        parsed["_file_modified"] = fp_data["file_modified"]
        parsed["_file_size"] = fp_data["file_size"]
        parsed_all[rel] = parsed

        parse_stats["total"] += 1
        if parsed["parse_errors"]:
            parse_stats["con_errors"] += 1
        elif parsed["parse_warnings"]:
            parse_stats["con_warnings"] += 1
        else:
            parse_stats["ok"] += 1

        if not parsed["empresa"]:
            parse_stats["sin_empresa"] += 1
        if not parsed["cargo"]:
            parse_stats["sin_cargo"] += 1
        if parsed["senal_humana"]:
            parse_stats["con_analisis"] += 1
        if parsed["resp_msg1_texto"]:
            parse_stats["con_respuesta_msg1"] += 1
        if parsed["msg2_texto"]:
            parse_stats["con_msg2"] += 1
        if parsed["seg1_texto"]:
            parse_stats["con_seg1"] += 1

    # Guardar cache raw para inspeccion
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(parsed_all, fh, ensure_ascii=False, indent=2)

    # Reporte de parsing
    total = parse_stats["total"]
    print("")
    print("=" * 60)
    print(f"  HITO 3 — PARSE REPORT  (parser v{PARSER_VERSION})")
    print("=" * 60)
    print(f"  Total parseados   : {total}")
    print(f"  Sin errores       : {parse_stats['ok']}")
    print(f"  Con warnings      : {parse_stats['con_warnings']}")
    print(f"  Con errores       : {parse_stats['con_errors']}")
    print(f"  ---")
    print(f"  Sin empresa       : {parse_stats['sin_empresa']}")
    print(f"  Sin cargo         : {parse_stats['sin_cargo']}")
    print(f"  Con analisis      : {parse_stats['con_analisis']}")
    print(f"  Con resp MSG1     : {parse_stats['con_respuesta_msg1']}")
    print(f"  Con MSG2          : {parse_stats['con_msg2']}")
    print(f"  Con SEG1          : {parse_stats['con_seg1']}")
    print(f"  ---")
    if total > 0:
        resp_rate = round(parse_stats["con_respuesta_msg1"] / total * 100, 1)
        msg2_rate = round(parse_stats["con_msg2"] / total * 100, 1)
        print(f"  Tasa respuesta    : {resp_rate}%")
        print(f"  Tasa MSG2         : {msg2_rate}%")
    print("=" * 60)

    # ── HITO 4: Normalize ────────────────────────────────────────────────────
    from collections import Counter
    from builders.normalizer import (
        detect_sector, detect_seniority, detect_stage,
        detect_resultado, detect_engagement, detect_variante_msg1,
    )

    stage_ctr: Counter = Counter()
    sector_ctr: Counter = Counter()
    seniority_ctr: Counter = Counter()
    resultado_ctr: Counter = Counter()
    engagement_ctr: Counter = Counter()
    variante_ctr: Counter = Counter()

    for _key, _raw in parsed_all.items():
        _st = detect_stage(_raw.get("estado", ""), _raw)
        stage_ctr[_st] += 1
        sector_ctr[detect_sector(_raw.get("empresa", ""), _raw.get("cargo", ""),
                                  _raw.get("sector", ""))] += 1
        seniority_ctr[detect_seniority(_raw.get("cargo", ""))] += 1
        _estado = _raw.get("estado", "")
        _call = any(kw in _estado.lower() for kw in ["reunion agendada", "call agendada"])
        _cerrado = any(kw in _estado.lower() for kw in ["cerrada", "cerrado"])
        resultado_ctr[detect_resultado(
            _st,
            bool(_raw.get("resp_msg1_texto")),
            bool(_raw.get("msg3_texto")) or _st >= 3,
            _call, _cerrado,
        )] += 1
        engagement_ctr[detect_engagement(_raw)] += 1
        variante_ctr[detect_variante_msg1(_raw.get("msg1_texto", ""))] += 1

    def _pct(n): return f"{round(n/total*100,1)}%"

    print("")
    print("=" * 60)
    print(f"  HITO 4 — NORMALIZE REPORT")
    print("=" * 60)
    print("  SECTOR:")
    for k, v in sector_ctr.most_common():
        print(f"    {_pct(v):6s}  {k}")
    print("  SENIORITY:")
    for k, v in seniority_ctr.most_common():
        print(f"    {_pct(v):6s}  {k}")
    print("  STAGE:")
    for k in sorted(stage_ctr.keys()):
        print(f"    Stage {k}: {stage_ctr[k]:3d}  {_pct(stage_ctr[k])}")
    print("  RESULTADO:")
    for k, v in resultado_ctr.most_common():
        print(f"    {_pct(v):6s}  {k}")
    print("  ENGAGEMENT:")
    for k, v in engagement_ctr.most_common():
        print(f"    {_pct(v):6s}  {k}")
    print("  VARIANTE MSG1:")
    for k, v in variante_ctr.most_common():
        print(f"    {_pct(v):6s}  {k}")
    print(f"  ---")
    print(f"  Cache: {CACHE_PATH}")
    print("=" * 60)

    # ── HITO 5: Dataset ──────────────────────────────────────────────────────
    from datetime import datetime, timezone
    from builders.index_builder import (
        load_registry, save_registry, resolve_id,
        save_conversation, build_index,
    )
    from builders.contacts_builder import (
        load_historial, load_contacts_registry, save_contacts_registry,
        resolve_contact_id, normalize_contact, detect_tiene_md,
        save_contact, build_contacts_index,
    )
    from builders.normalizer import normalize
    from builders.manifest_builder import build_manifest
    from builders.export_builder import export_csv

    now = datetime.now(timezone.utc).isoformat()

    # norm_name helper (misma lógica que contacts_builder.norm_name)
    import re as _re
    _NM_ACCENT = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    def _norm_name(s: str) -> str:
        return _re.sub(r"\s+", " ", (s or "").lower().translate(_NM_ACCENT).strip())

    # Fase A — pre-asignar ctc_ids desde historial (necesario antes de las conversaciones)
    historial = load_historial()
    ctc_registry = load_contacts_registry()
    slug_to_ctc_id: dict = {}
    hist_name_to_ctc_id: dict = {}  # norm_name → ctc_id para lookup en Phase B
    for _entry in historial:
        _slug = _entry.get("id", "")
        if _slug:
            _ctc_id_tmp = resolve_contact_id(_slug, ctc_registry)
            slug_to_ctc_id[_slug] = _ctc_id_tmp
            _hist_name = _entry.get("name") or _entry.get("nombre", "")
            if _hist_name:
                hist_name_to_ctc_id[_norm_name(_hist_name)] = _ctc_id_tmp

    # Fase B — construir conversaciones
    conv_registry = load_registry()
    conv_records = []
    slug_to_conv_id: dict = {}
    conv_errors = []

    for _rel_key, _raw in parsed_all.items():
        _src = _raw.get("_source_file", _rel_key.replace("\\", "/"))
        _stem = _src.split("/")[-1].replace(".md", "")
        _hash = _raw.get("_fingerprint", "")
        _contact_id = (
            slug_to_ctc_id.get(_stem)
            or hist_name_to_ctc_id.get(_norm_name(_raw.get("nombre", "")))
            or "ctc_UNKNOWN"
        )
        _conv_id = resolve_id(_src, _hash, conv_registry)

        _source_info = {
            "_source_file": _src,
            "_fingerprint": _hash,
            "file_modified": _raw.get("_file_modified", ""),
            "file_size": _raw.get("_file_size", 0),
        }
        try:
            _record = normalize(_raw, _conv_id, _contact_id, _source_info, created_at=now)
            conv_records.append(_record)
            save_conversation(_record)
            slug_to_conv_id[_stem] = _conv_id
        except Exception as _e:
            logging.warning(f"normalize error {_src}: {_e}")
            conv_errors.append({"file": _src, "error": str(_e)})

    save_registry(conv_registry)
    build_index(conv_records)

    # Fase C — construir contactos (linking por nombre normalizado)
    name_to_conv_id: dict = {
        _norm_name(_r.metadata.nombre): _r.conversation_id
        for _r in conv_records if _r.metadata.nombre
    }
    md_names = set(name_to_conv_id.keys())

    ctc_records = []
    for _entry in historial:
        _slug = _entry.get("id", "")
        _ctc_id = slug_to_ctc_id.get(_slug, "")
        if not _ctc_id:
            continue
        _ctc = normalize_contact(_entry, _ctc_id, now)
        _ctc.tiene_md = detect_tiene_md(_ctc.nombre, _slug, md_names)
        _ctc.conversation_id = name_to_conv_id.get(_norm_name(_ctc.nombre))
        ctc_records.append(_ctc)
        save_contact(_ctc)

    save_contacts_registry(ctc_registry)
    build_contacts_index(ctc_records)

    # Fase D — manifest + CSV
    build_manifest(conv_records, conv_errors, "full", t0, {})
    csv_rows = export_csv()

    # Reporte HITO 5
    con_md = sum(1 for c in ctc_records if c.tiene_md)
    sin_md = len(ctc_records) - con_md
    print("")
    print("=" * 60)
    print(f"  HITO 5 — DATASET")
    print("=" * 60)
    print(f"  Conversaciones  : {len(conv_records)} conv_XXXXXX.json")
    print(f"  Contactos       : {len(ctc_records)} ctc_XXXXXX.json")
    print(f"  Con .md linkeado: {con_md}  ({round(con_md/len(ctc_records)*100,1)}%)")
    print(f"  Sin .md         : {sin_md}  (solo en historial)")
    print(f"  Errores HITO 5  : {len(conv_errors)}")
    print(f"  CSV exportado   : {csv_rows} filas")
    print(f"  ---")
    print(f"  Manifest        : {MANIFEST_PATH}")
    print("=" * 60)

    # ── HITO 6: Reports ──────────────────────────────────────────────────────
    from builders.report_builder import build_coverage_report, build_quality_report
    from config import COVERAGE_REPORT_PATH, QUALITY_REPORT_PATH

    build_coverage_report()
    build_quality_report()

    print("")
    print("=" * 60)
    print(f"  HITO 6 — REPORTS")
    print("=" * 60)
    print(f"  Coverage: {COVERAGE_REPORT_PATH}")
    print(f"  Quality : {QUALITY_REPORT_PATH}")
    print("=" * 60)

    # ── HITO 7: Intelligence ─────────────────────────────────────────────────
    from builders.intelligence_builder import build_intelligence
    from builders.intelligence_builder import INTELLIGENCE_REPORT_PATH, SUMMARY_PATH

    build_intelligence()

    print("")
    print("=" * 60)
    print(f"  HITO 7 — INTELLIGENCE")
    print("=" * 60)
    print(f"  Summary : {SUMMARY_PATH}")
    print(f"  Report  : {INTELLIGENCE_REPORT_PATH}")
    print("=" * 60)

    t_total = time.time() - t0
    logging.info(
        f"FULL BUILD completo en {t_total:.2f}s — "
        f"{total} archivos — {parse_stats['con_errors']} errores"
    )
    logging.info("FULL BUILD — HITO 3+4+5+6+7 completo.")


def cmd_update() -> None:
    """Build incremental: solo archivos con hash cambiado o nuevos."""
    import json
    from builders.crawler import discover_files, report_discovery, print_report
    from builders.fingerprinter import compute_fingerprint, has_changed
    from builders.parser import parse_file
    from config import CACHE_PATH, CONVERSACIONES_ROOT

    t0 = time.time()
    logging.info(f"Memoria Comercial v{PARSER_VERSION} — UPDATE BUILD iniciado")
    logging.info(f"Fuente: {CONVERSACIONES_ROOT}")

    # Crawl
    files = discover_files()
    report = report_discovery(files)
    print_report(report)

    # Cargar cache existente
    cached: dict = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
        except Exception:
            cached = {}

    # Parsear solo archivos cambiados o nuevos
    updated = 0
    for file_path in files:
        rel = os.path.relpath(file_path, os.path.dirname(CONVERSACIONES_ROOT))
        rel_key = rel.replace("\\", "/")

        fp_data = compute_fingerprint(file_path)
        stored_hash = (cached.get(rel_key) or {}).get("_fingerprint", "")
        if not has_changed(file_path, stored_hash):
            continue

        parsed = parse_file(file_path)
        parsed["_source_file"] = rel_key
        parsed["_fingerprint"] = fp_data["file_hash"]
        cached[rel_key] = parsed
        updated += 1

    # Guardar cache actualizada
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cached, fh, ensure_ascii=False, indent=2)

    t_total = time.time() - t0
    print(f"\n[Memoria Comercial] UPDATE > {updated} archivos actualizados en {t_total:.2f}s")
    logging.info(
        f"UPDATE BUILD completo en {t_total:.2f}s — {updated} archivos actualizados"
    )


def cmd_export() -> None:
    """Regenera conversations.csv desde JSON existente. JSON es fuente de verdad."""
    logging.info(f"Memoria Comercial v{PARSER_VERSION} — EXPORT")
    logging.info("EXPORT — HITO 5: no implementado todavia.")
    print("[Memoria Comercial] EXPORT > HITO 5: no implementado todavia")


def cmd_intel() -> None:
    """Regenera intelligence patterns y report desde conversations_index.json existente."""
    from builders.intelligence_builder import build_intelligence
    from builders.intelligence_builder import INTELLIGENCE_REPORT_PATH, SUMMARY_PATH

    logging.info(f"Memoria Comercial v{PARSER_VERSION} — INTEL")
    build_intelligence()
    print(f"[Memoria Comercial] INTEL > summary : {SUMMARY_PATH}")
    print(f"[Memoria Comercial] INTEL > report  : {INTELLIGENCE_REPORT_PATH}")
    logging.info("INTEL completo.")


def cmd_report() -> None:
    """Regenera coverage_report.md y quality_report.md desde JSON existente."""
    from builders.report_builder import build_coverage_report, build_quality_report
    from config import COVERAGE_REPORT_PATH, QUALITY_REPORT_PATH

    logging.info(f"Memoria Comercial v{PARSER_VERSION} — REPORT")
    build_coverage_report()
    build_quality_report()
    print(f"[Memoria Comercial] REPORT > coverage: {COVERAGE_REPORT_PATH}")
    print(f"[Memoria Comercial] REPORT > quality : {QUALITY_REPORT_PATH}")
    logging.info("REPORT completo.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(
        prog="run.py",
        description=f"Memoria Comercial — Hint Media LinkedIn  (v{PARSER_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Versiones:\n"
            f"  schema:  {SCHEMA_VERSION}\n"
            f"  parser:  {PARSER_VERSION}\n"
            f"  dataset: {DATASET_VERSION}"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full",   action="store_true", help="Full rebuild desde cero")
    group.add_argument("--update", action="store_true", help="Build incremental")
    group.add_argument("--export", action="store_true", help="Regenerar CSV desde JSON")
    group.add_argument("--report", action="store_true", help="Regenerar reportes")
    group.add_argument("--intel",  action="store_true", help="Regenerar intelligence patterns")

    args = parser.parse_args()

    if args.full:
        cmd_full()
    elif args.update:
        cmd_update()
    elif args.export:
        cmd_export()
    elif args.report:
        cmd_report()
    elif args.intel:
        cmd_intel()


if __name__ == "__main__":
    main()
