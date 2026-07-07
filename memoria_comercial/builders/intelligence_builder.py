"""
intelligence_builder.py — HITO 7: Commercial Intelligence Engine.

Lee conversations_index.json (lightweight, sin textos).
Genera patrones de conversion por sector, seniority y variante MSG1.
Output: intelligence/patterns/*.json + intelligence/summary.json
        reports/intelligence_report.md

Sin IA. Solo estadistica pura del dataset.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    CONVERSATIONS_INDEX_PATH,
    INTELLIGENCE_DIR,
    INTELLIGENCE_PATTERNS_DIR,
    REPORTS_DIR,
)

INTELLIGENCE_REPORT_PATH = os.path.join(REPORTS_DIR, "intelligence_report.md")
SUMMARY_PATH = os.path.join(INTELLIGENCE_DIR, "summary.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def _pct(f: float) -> str:
    return f"{f * 100:.1f}%"


def _load_index() -> List[Dict]:
    with open(CONVERSATIONS_INDEX_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("records", [])


def _save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


# ── Analysers ─────────────────────────────────────────────────────────────────

def _analyse_group(records: List[Dict]) -> Dict:
    """Metricas de conversion para un grupo de registros."""
    total = len(records)
    respondio = sum(1 for r in records if r.get("respondio_msg1"))
    dossier = sum(1 for r in records if r.get("dossier_enviado"))
    call = sum(1 for r in records if r.get("call_agendada"))
    en_proceso = sum(1 for r in records if r.get("resultado_final") == "EN_PROCESO")
    sin_resp = sum(1 for r in records if r.get("resultado_final") == "SIN_RESPUESTA")
    cerrado = sum(1 for r in records if r.get("resultado_final") == "CERRADO_SIN_INTERES")
    reunion = sum(1 for r in records if r.get("resultado_final") == "REUNION")

    return {
        "total": total,
        "respondio_msg1": respondio,
        "dossier_enviado": dossier,
        "call_agendada": call,
        "response_rate": _rate(respondio, total),
        "dossier_rate": _rate(dossier, total),
        "call_rate": _rate(call, total),
        "dossier_from_response": _rate(dossier, respondio),
        "call_from_dossier": _rate(call, dossier),
        "by_resultado": {
            "EN_PROCESO": en_proceso,
            "SIN_RESPUESTA": sin_resp,
            "CERRADO_SIN_INTERES": cerrado,
            "REUNION": reunion,
        },
    }


def build_funnel(records: List[Dict]) -> Dict:
    funnel = _analyse_group(records)
    funnel["generated_at"] = datetime.now().isoformat()

    # Por mes
    by_month: Dict[str, List] = defaultdict(list)
    for r in records:
        src = r.get("source_file", "")
        month = "julio" if "julio" in src else "junio" if "junio" in src else "otro"
        by_month[month].append(r)

    funnel["by_month"] = {
        month: _analyse_group(recs)
        for month, recs in sorted(by_month.items())
    }

    _save_json(os.path.join(INTELLIGENCE_PATTERNS_DIR, "funnel.json"), funnel)
    return funnel


def build_by_sector(records: List[Dict]) -> Dict:
    by_sector: Dict[str, List] = defaultdict(list)
    for r in records:
        sector = r.get("sector") or "DESCONOCIDO"
        by_sector[sector].append(r)

    result = {}
    for sector, recs in sorted(by_sector.items()):
        result[sector] = _analyse_group(recs)

    _save_json(os.path.join(INTELLIGENCE_PATTERNS_DIR, "by_sector.json"), result)
    return result


def build_by_seniority(records: List[Dict]) -> Dict:
    by_sen: Dict[str, List] = defaultdict(list)
    for r in records:
        sen = r.get("seniority") or "DESCONOCIDO"
        by_sen[sen].append(r)

    result = {}
    for sen, recs in sorted(by_sen.items()):
        result[sen] = _analyse_group(recs)

    _save_json(os.path.join(INTELLIGENCE_PATTERNS_DIR, "by_seniority.json"), result)
    return result


def build_by_variant(records: List[Dict]) -> Dict:
    by_var: Dict[str, List] = defaultdict(list)
    for r in records:
        var = r.get("variante_msg1") or "DESCONOCIDO"
        by_var[var].append(r)

    result = {}
    for var, recs in sorted(by_var.items()):
        result[var] = _analyse_group(recs)

    _save_json(os.path.join(INTELLIGENCE_PATTERNS_DIR, "by_variant.json"), result)
    return result


def build_by_engagement(records: List[Dict]) -> Dict:
    by_eng: Dict[str, List] = defaultdict(list)
    for r in records:
        eng = r.get("engagement_level") or "DESCONOCIDO"
        by_eng[eng].append(r)

    result = {}
    for eng, recs in sorted(by_eng.items()):
        result[eng] = _analyse_group(recs)

    _save_json(os.path.join(INTELLIGENCE_PATTERNS_DIR, "by_engagement.json"), result)
    return result


# ── Summary ───────────────────────────────────────────────────────────────────

def _best_by(analysis: Dict, metric: str, min_total: int = 5) -> Optional[str]:
    """Retorna la clave con mayor valor de metric, con minimo de registros."""
    candidates = [(k, v[metric]) for k, v in analysis.items() if v["total"] >= min_total]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[1])[0]


def build_summary(funnel: Dict, by_sector: Dict, by_seniority: Dict, by_variant: Dict) -> Dict:
    best_sector = _best_by(by_sector, "response_rate")
    best_sector_dossier = _best_by(by_sector, "dossier_rate")
    best_seniority = _best_by(by_seniority, "response_rate")
    best_variant = _best_by(by_variant, "response_rate")

    # Etapa con mayor drop-off
    total = funnel["total"]
    respondio = funnel["respondio_msg1"]
    dossier = funnel["dossier_enviado"]
    call = funnel["call_agendada"]
    drops = {
        "MSG1→Respuesta": total - respondio,
        "Respuesta→Dossier": respondio - dossier,
        "Dossier→Call": dossier - call,
    }
    biggest_dropoff = max(drops, key=lambda k: drops[k])

    summary = {
        "generated_at": datetime.now().isoformat(),
        "global": {
            "total_conversations": total,
            "response_rate": funnel["response_rate"],
            "dossier_rate": funnel["dossier_rate"],
            "call_rate": funnel["call_rate"],
        },
        "best_performers": {
            "sector_by_response": best_sector,
            "sector_by_dossier": best_sector_dossier,
            "seniority_by_response": best_seniority,
            "variant_by_response": best_variant,
        },
        "funnel_drops": drops,
        "biggest_dropoff": biggest_dropoff,
    }

    _save_json(SUMMARY_PATH, summary)
    return summary


# ── Markdown report ───────────────────────────────────────────────────────────

def build_intelligence_report(
    funnel: Dict,
    by_sector: Dict,
    by_seniority: Dict,
    by_variant: Dict,
    by_engagement: Dict,
    summary: Dict,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = funnel["total"]

    lines = [
        "# Intelligence Report",
        "",
        f"_Generado: {now} — {total} conversaciones analizadas_",
        "",
        "---",
        "",
        "## Funnel Global",
        "",
        "| Etapa | Cantidad | Tasa |",
        "|-------|----------|------|",
        f"| Contactados | {total} | 100% |",
        f"| Respondieron MSG1 | {funnel['respondio_msg1']} | {_pct(funnel['response_rate'])} |",
        f"| Dossier enviado | {funnel['dossier_enviado']} | {_pct(funnel['dossier_rate'])} |",
        f"| Call agendada | {funnel['call_agendada']} | {_pct(funnel['call_rate'])} |",
        "",
        f"**Mayor drop-off:** {summary['biggest_dropoff']} "
        f"({summary['funnel_drops'][summary['biggest_dropoff']]} contactos perdidos)",
        "",
        "### Conversion entre etapas",
        "",
        "| De → A | Tasa |",
        "|--------|------|",
        f"| Respuesta → Dossier | {_pct(funnel['dossier_from_response'])} |",
        f"| Dossier → Call | {_pct(funnel['call_from_dossier'])} |",
        "",
        "---",
        "",
        "## Por Mes",
        "",
        "| Mes | Total | Response Rate | Dossier Rate |",
        "|-----|-------|---------------|--------------|",
    ]

    for month, stats in sorted(funnel.get("by_month", {}).items()):
        lines.append(
            f"| {month} | {stats['total']} | {_pct(stats['response_rate'])} | {_pct(stats['dossier_rate'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Por Sector",
        "",
        "| Sector | Total | Response Rate | Dossier Rate | Call Rate |",
        "|--------|-------|---------------|--------------|-----------|",
    ]

    for sector, stats in sorted(by_sector.items(), key=lambda x: -x[1]["response_rate"]):
        lines.append(
            f"| {sector} | {stats['total']} | {_pct(stats['response_rate'])} "
            f"| {_pct(stats['dossier_rate'])} | {_pct(stats['call_rate'])} |"
        )

    best_s = summary["best_performers"]["sector_by_response"]
    best_sd = summary["best_performers"]["sector_by_dossier"]
    if best_s:
        sr = by_sector[best_s]["response_rate"]
        lines.append(f"\n**Mejor sector (respuesta):** {best_s} — {_pct(sr)}")
    if best_sd and best_sd != best_s:
        sdr = by_sector[best_sd]["dossier_rate"]
        lines.append(f"**Mejor sector (dossier):** {best_sd} — {_pct(sdr)}")

    lines += [
        "",
        "---",
        "",
        "## Por Seniority",
        "",
        "| Seniority | Total | Response Rate | Dossier Rate |",
        "|-----------|-------|---------------|--------------|",
    ]

    for sen, stats in sorted(by_seniority.items(), key=lambda x: -x[1]["response_rate"]):
        lines.append(
            f"| {sen} | {stats['total']} | {_pct(stats['response_rate'])} | {_pct(stats['dossier_rate'])} |"
        )

    best_sn = summary["best_performers"]["seniority_by_response"]
    if best_sn:
        snr = by_seniority[best_sn]["response_rate"]
        lines.append(f"\n**Mejor seniority:** {best_sn} — {_pct(snr)}")

    lines += [
        "",
        "---",
        "",
        "## Por Variante MSG1",
        "",
        "| Variante | Total | Response Rate | Dossier Rate |",
        "|----------|-------|---------------|--------------|",
    ]

    for var, stats in sorted(by_variant.items(), key=lambda x: -x[1]["response_rate"]):
        lines.append(
            f"| {var} | {stats['total']} | {_pct(stats['response_rate'])} | {_pct(stats['dossier_rate'])} |"
        )

    best_v = summary["best_performers"]["variant_by_response"]
    if best_v:
        vr = by_variant[best_v]["response_rate"]
        lines.append(f"\n**Mejor variante:** {best_v} — {_pct(vr)}")

    lines += [
        "",
        "---",
        "",
        "## Por Engagement Level",
        "",
        "| Engagement | Total | Dossier Rate | Call Rate |",
        "|------------|-------|--------------|-----------|",
    ]

    eng_order = ["HIGH", "MEDIUM", "LOW", "DESCONOCIDO"]
    for eng in eng_order:
        if eng not in by_engagement:
            continue
        stats = by_engagement[eng]
        lines.append(
            f"| {eng} | {stats['total']} | {_pct(stats['dossier_rate'])} | {_pct(stats['call_rate'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Insights Accionables",
        "",
    ]

    # Generate insights
    insights = []

    # Insight 1: response rate global
    rr = funnel["response_rate"]
    if rr < 0.20:
        insights.append(f"Response rate global baja ({_pct(rr)}). Revisar ángulos de MSG1 — objetivo minimo 25%.")
    elif rr > 0.35:
        insights.append(f"Response rate global solida ({_pct(rr)}). Mantener estructura de MSG1 actual.")
    else:
        insights.append(f"Response rate global aceptable ({_pct(rr)}). Margen de mejora en MSG1.")

    # Insight 2: biggest drop-off
    dropoff = summary["biggest_dropoff"]
    drops = summary["funnel_drops"]
    insights.append(
        f"Mayor perdida en '{dropoff}' ({drops[dropoff]} contactos). "
        f"Priorizar mejora en esa etapa."
    )

    # Insight 3: best sector
    if best_s:
        sr = by_sector[best_s]["response_rate"]
        total_s = by_sector[best_s]["total"]
        insights.append(
            f"Sector con mejor respuesta: {best_s} ({_pct(sr)} sobre {total_s} contactos). "
            f"Aumentar volumen en ese sector."
        )

    # Insight 4: best seniority
    if best_sn:
        snr = by_seniority[best_sn]["response_rate"]
        insights.append(
            f"Seniority mas receptivo: {best_sn} ({_pct(snr)}). "
            f"Priorizar ese nivel en la prospección."
        )

    # Insight 5: best variant
    if best_v:
        vr = by_variant[best_v]["response_rate"]
        insights.append(
            f"Variante MSG1 con mejor tasa: {best_v} ({_pct(vr)}). "
            f"Escalar ese estilo de apertura."
        )

    # Insight 6: dossier conversion
    dfr = funnel["dossier_from_response"]
    insights.append(
        f"De quienes responden, {_pct(dfr)} acepta el dossier. "
        + ("Alta conversion post-respuesta." if dfr > 0.5 else "Oportunidad de mejora en MSG2.")
    )

    for i, insight in enumerate(insights, 1):
        lines.append(f"{i}. {insight}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(INTELLIGENCE_REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def build_intelligence() -> None:
    records = _load_index()

    funnel = build_funnel(records)
    by_sector = build_by_sector(records)
    by_seniority = build_by_seniority(records)
    by_variant = build_by_variant(records)
    by_engagement = build_by_engagement(records)
    summary = build_summary(funnel, by_sector, by_seniority, by_variant)
    build_intelligence_report(funnel, by_sector, by_seniority, by_variant, by_engagement, summary)
