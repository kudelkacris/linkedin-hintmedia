# -*- coding: utf-8 -*-
"""
alertas.py - Alertas de seguimiento diarias.

Escanea conversaciones/*.md, detecta la ultima accion y su fecha,
y avisa que contactos necesitan accion hoy.

Reglas:
    Dossier enviado  + 3 dias sin respuesta  -> enviar SEG1
    SEG1 enviado     + 5 dias sin respuesta  -> enviar SEG2
    SEG2 enviado     + 7 dias sin respuesta  -> decidir cierre
    MSG2 enviado     + 7 dias sin respuesta  -> evaluar seguimiento

Uso:
    python alertas.py             # alertas de hoy
    python alertas.py --todas     # incluye contactos en espera (aun sin vencer)
    python alertas.py --json      # salida JSON (para servidor.py)
"""
import sys
import io
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, date

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
DATE_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{2})\b")

# (patron sobre Estado, etiqueta, dias de espera, accion sugerida)
REGLAS = [
    (r"reuni[oó]n|call agendada|agendada",           "REUNION",  None, None),
    (r"cerrad|no interes|descartad|sin interes",     "CERRADA",  None, None),
    (r"seg.?2|seguimiento 2",                        "SEG2",     7,  "decidir cierre o ultimo toque"),
    (r"seg.?1|seguimiento 1",                        "SEG1",     5,  "enviar SEG2"),
    (r"dossier",                                     "DOSSIER",  3,  "enviar SEG1"),
    (r"msg.?2",                                      "MSG2",     7,  "evaluar seguimiento"),
    (r"msg.?1",                                      "MSG1",     None, None),
]


def parse_fecha(s):
    m = DATE_RE.search(s)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), 2000 + int(m.group(3))
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def ultima_fecha(texto):
    fechas = [parse_fecha(m.group(0)) for m in DATE_RE.finditer(texto)]
    fechas = [f for f in fechas if f]
    return max(fechas) if fechas else None


def analizar(md_path, hoy):
    texto = md_path.read_text(encoding="utf-8", errors="replace")
    estados = re.findall(r"\*\*Estado:\*\*\s*(.+)", texto)
    estado = estados[-1].strip() if estados else ""
    nombre_m = re.search(r"^#\s+(.+)", texto, re.M)
    nombre = nombre_m.group(1).strip() if nombre_m else md_path.stem

    etapa, espera, accion = None, None, None
    for patron, et, dias, acc in REGLAS:
        if re.search(patron, estado, re.I):
            etapa, espera, accion = et, dias, acc
            break

    if etapa in (None, "MSG1", "CERRADA", "REUNION"):
        return None

    fecha = parse_fecha(estado) or ultima_fecha(texto)
    if not fecha:
        return {"nombre": nombre, "etapa": etapa, "dias": None,
                "accion": accion, "estado": estado, "vencida": True,
                "archivo": str(md_path.relative_to(BASE))}

    dias = (hoy - fecha).days
    return {"nombre": nombre, "etapa": etapa, "dias": dias,
            "accion": accion, "estado": estado, "vencida": dias >= espera,
            "archivo": str(md_path.relative_to(BASE))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    hoy = date.today()
    alertas = []
    for md in sorted((BASE / "conversaciones").rglob("*.md")):
        r = analizar(md, hoy)
        if r and (r["vencida"] or args.todas):
            alertas.append(r)

    # mas dias sin accion primero; sin fecha al final
    alertas.sort(key=lambda a: -(a["dias"] if a["dias"] is not None else -1))

    if args.json:
        print(json.dumps(alertas, ensure_ascii=False, indent=2))
        return

    if not alertas:
        print(f"HOY ({hoy:%d/%m}): sin alertas pendientes.")
        return

    print(f"HOY ({hoy:%d/%m}): {sum(1 for a in alertas if a['vencida'])} contactos necesitan accion\n")
    for a in alertas:
        dias = f"{a['dias']}d" if a["dias"] is not None else "sin fecha"
        marca = "!" if a["vencida"] else " "
        print(f" {marca} [{a['etapa']:7}] {a['nombre']:35} {dias:>9}  -> {a['accion']}")


if __name__ == "__main__":
    main()
