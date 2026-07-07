"""
contact.py — ContactRecord: Nivel 1 de la Memoria Comercial.

Representa una entidad comercial.
Fuente de datos: historial.json (541 registros).

Un CONTACTO puede existir sin conversación (tiene_md = False).
Una CONVERSACIÓN siempre pertenece a un CONTACTO (contact_id obligatorio).

Regla fundamental de la arquitectura:
  CONTACTS   es el modelo del negocio   — quién es, en qué stage está.
  CONVERSATIONS es la evidencia comercial — qué se dijo, cómo respondió.

Se serializa como ctc_XXXXXX.json en dataset/contacts/.
"""
from dataclasses import dataclass
from typing import Optional

from .fields import Sector, Seniority


@dataclass
class ContactRecord:
    """
    Nivel 1 de la Memoria Comercial.
    Contiene solo metadatos — nunca texto de conversación.
    """

    # ── Identificación ────────────────────────────────────────────────────────
    contact_id: str         # ctc_000001 — permanente, nunca cambia
    schema_version: str
    created_at: str         # ISO 8601 UTC — primera vez construido
    updated_at: str         # ISO 8601 UTC — última actualización

    # ── Datos del contacto (raw del historial.json) ───────────────────────────
    nombre: str
    empresa: str
    cargo: str
    pais: str
    sector_raw: str         # tal como viene en historial.json (texto libre)

    # ── CRM ───────────────────────────────────────────────────────────────────
    stage: int              # 1–6
    stage_texto: str        # "MSG2 enviado", "Dossier enviado", etc.
    fecha: str              # DD/MM/YY — fecha del último movimiento
    email: Optional[str]    # email para dossier si fue por mail

    # ── Campos normalizados ───────────────────────────────────────────────────
    sector_norm: Sector     # normalizado con enum
    seniority: Seniority    # inferido desde cargo

    # ── Link al sistema de conversaciones ─────────────────────────────────────
    tiene_md: bool                  # True si existe .md en conversaciones/
    conversation_id: Optional[str]  # "conv_000001" si tiene_md, None si no

    # ── Trazabilidad al historial.json original ───────────────────────────────
    historial_slug: str     # el campo 'id' del historial.json (slug original)

    # ── Campos reservados — CRM temporal ─────────────────────────────────────
    # Se calcularán en HITO 5 al cruzar contacts + conversations:
    #   conversation_count: int        cuántas conversaciones tiene este contacto
    #   first_contact_date: str        ISO 8601 — fecha del primer MSG1 (historial.json fecha)
    #   last_activity_date: str        ISO 8601 — última actividad registrada
    #   last_stage_change: str         ISO 8601 — cuándo cambió de stage por última vez
    # Permiten calcular: velocidad comercial, contactos dormidos, tiempo MSG1→reunión.

    # ── Campos reservados — Commercial Intelligence Engine ────────────────────
    # Se llenarán en fases futuras:
    #   commercial_score: float        probabilidad de conversión estimada
    #   recommended_next_action: str   acción recomendada (SEG1, SEG2, reunión, cerrar)
    #   days_in_stage: int             días en el stage actual
    #   last_interaction: str          ISO 8601 de la última actividad registrada
    #   recontact_date: str            fecha recomendada de siguiente contacto
