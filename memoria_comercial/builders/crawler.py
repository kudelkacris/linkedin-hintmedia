"""
crawler.py — Descubrimiento recursivo de archivos .md.

Responsabilidad única: encontrar TODOS los archivos .md bajo conversaciones/,
sin importar cuántas subcarpetas existan ni cómo se llamen.
Si mañana aparece conversaciones/agosto/, lo detecta automáticamente.
Sin parseo. Sin normalización. Solo descubrimiento + reporte.
"""
import os
import glob
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONVERSACIONES_ROOT, MD_EXTENSION

# Mapa de nombres de carpeta → número de mes (2 dígitos)
# Si aparece una carpeta con nombre diferente, cae en la clave original
_MONTH_NAMES = {
    "enero": "01", "february": "02", "febrero": "02",
    "marzo": "03", "march": "03",
    "abril": "04", "april": "04",
    "mayo": "05", "may": "05",
    "junio": "06", "june": "06",
    "julio": "07", "july": "07",
    "agosto": "08", "august": "08",
    "septiembre": "09", "september": "09",
    "octubre": "10", "october": "10",
    "noviembre": "11", "november": "11",
    "diciembre": "12", "december": "12",
}


def discover_files(conversaciones_root: str = None) -> List[str]:
    """
    Recorre conversaciones_root recursivamente.
    Retorna lista de paths absolutos a todos los .md encontrados.
    Ignora cualquier otro tipo de archivo.
    Orden determinista: sorted() por path completo.
    """
    root = conversaciones_root or CONVERSACIONES_ROOT
    pattern = os.path.join(root, "**", "*" + MD_EXTENSION)
    files = glob.glob(pattern, recursive=True)
    return sorted(files)


def report_discovery(files: List[str], conversaciones_root: str = None) -> Dict:
    """
    Construye resumen del descubrimiento sin leer el contenido de los archivos.

    Retorna:
    {
      "total": int,
      "by_folder": {"junio": 172, "julio": 104, ...},
      "by_month":  {"2026-06": 172, "2026-07": 104, ...},
      "errors": [{"file": str, "error": str}, ...]
    }
    """
    root = conversaciones_root or CONVERSACIONES_ROOT
    by_folder: Dict[str, int] = {}
    errors: List[Dict] = []

    for f in files:
        try:
            rel = Path(f).relative_to(root)
            # primer segmento del path relativo = nombre de carpeta
            folder = rel.parts[0] if len(rel.parts) > 1 else "_raiz"
            by_folder[folder] = by_folder.get(folder, 0) + 1
        except Exception as e:
            errors.append({"file": f, "error": str(e)})

    by_month: Dict[str, int] = {}
    for folder, count in by_folder.items():
        month_key = _folder_to_month_key(folder)
        by_month[month_key] = by_month.get(month_key, 0) + count

    return {
        "total": len(files),
        "by_folder": dict(sorted(by_folder.items())),
        "by_month":  dict(sorted(by_month.items())),
        "errors": errors,
    }


def print_report(report: Dict) -> None:
    """Imprime el reporte de descubrimiento en consola."""
    sep = "-" * 40
    print(sep)
    print(f"  DISCOVERY REPORT")
    print(sep)
    print(f"  Total archivos .md encontrados: {report['total']}")
    print()

    print("  Por carpeta:")
    if report["by_folder"]:
        max_len = max(len(k) for k in report["by_folder"])
        for folder, count in sorted(report["by_folder"].items()):
            print(f"    {folder:<{max_len}}  {count:>4}")
    else:
        print("    (ninguna)")
    print()

    print("  Por mes:")
    if report["by_month"]:
        max_len = max(len(k) for k in report["by_month"])
        for month, count in sorted(report["by_month"].items()):
            print(f"    {month:<{max_len}}  {count:>4}")
    else:
        print("    (ninguno)")
    print()

    error_count = len(report["errors"])
    print(f"  Errores: {error_count}")
    if error_count:
        for err in report["errors"]:
            print(f"    [ERROR] {err['file']}: {err['error']}")
    print(sep)


def _folder_to_month_key(folder_name: str) -> str:
    """
    Convierte nombre de carpeta a clave de mes.
    "junio"  → "2026-06"
    "julio"  → "2026-07"
    Fallback: retorna el nombre original sin modificar.
    El año 2026 es la base actual; si el proyecto continúa en 2027+
    este mapping deberá actualizarse o inferirse desde las fechas del .md.
    """
    lower = folder_name.lower()
    for month_name, month_num in _MONTH_NAMES.items():
        if month_name in lower:
            return f"2026-{month_num}"
    return folder_name
