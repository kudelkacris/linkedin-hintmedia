"""
fingerprinter.py — Calcula hash, mtime y size de archivos .md.

Permite builds incrementales: si el hash no cambió, el archivo no se reprocesa.
Mitiga el riesgo de lectura concurrente con servidor.py:
si un archivo no puede leerse (locked, permiso, escrito a medias),
lanza OSError y el caller decide si skipear o logear.
"""
import hashlib
import os
import sys
from datetime import datetime, timezone
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HASH_ALGORITHM

_CHUNK_SIZE = 65_536   # 64 KB por chunk — eficiente para archivos grandes sin consumir mucha RAM


def compute_fingerprint(file_path: str) -> Dict:
    """
    Calcula fingerprint completo del archivo.
    Retorna:
    {
      "file_hash":     "sha256:abc123...",
      "file_modified": "2026-07-07T10:00:00+00:00",   ISO 8601 UTC
      "file_size":     2048                              bytes
    }
    Lanza OSError si el archivo no puede leerse (locked, sin permisos, etc.).
    """
    stat = os.stat(file_path)

    h = hashlib.new(HASH_ALGORITHM)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)

    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    return {
        "file_hash":     f"{HASH_ALGORITHM}:{h.hexdigest()}",
        "file_modified": mtime,
        "file_size":     stat.st_size,
    }


def has_changed(file_path: str, stored_hash: str) -> bool:
    """
    Compara el hash actual del archivo con el hash almacenado en id_registry.json.
    True  → archivo cambió, debe reprocesarse.
    False → sin cambios, puede saltarse en --update.

    Si el archivo no puede leerse, retorna True (conservador: reprocesar ante la duda).
    """
    try:
        fp = compute_fingerprint(file_path)
        return fp["file_hash"] != stored_hash
    except OSError:
        return True
